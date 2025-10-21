from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import os
import subprocess
import json
import atexit
import time
from threading import Lock

app = FastAPI(title="CTP Service", version="1.0.0")


# ==================== MdDaemon 客户端 ====================

class MdDaemonClient:
    """管理 md_daemon 守护进程的客户端"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.lock = Lock()
        self._started = False
    
    def start(self):
        """启动守护进程（应用启动时调用一次）"""
        if self._started:
            return
        
        front = os.getenv("CTP_MD_SERVER")
        broker = os.getenv("CTP_BROKER_ID")
        user = os.getenv("CTP_USER_ID")
        password = os.getenv("CTP_PASSWORD")
        
        if not all([front, broker, user, password]):
            raise ValueError("Missing CTP credentials in environment")
        
        # 启动守护进程
        self.process = subprocess.Popen(
            ["/usr/local/bin/md_daemon", front, broker, user, password],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # 行缓冲
            env={"LD_LIBRARY_PATH": "/usr/local/lib/ctp"}
        )
        
        self._started = True
        print("[INFO] MdDaemon started, waiting for login...")
        
        # 等待登录
        time.sleep(3)
        
        # 测试连接
        try:
            result = self.send_command("PING")
            if result.get("ok"):
                print("[INFO] MdDaemon ready!")
            else:
                print("[WARN] MdDaemon ping failed, but continuing...")
        except Exception as e:
            print(f"[WARN] MdDaemon ping error: {e}")
    
    def send_command(self, cmd: str, timeout: int = 10) -> dict:
        """发送命令并获取响应"""
        if not self.process:
            raise RuntimeError("Daemon not started")
        
        with self.lock:
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
                
                # 读取响应（简单方式，依赖行缓冲）
                response = self.process.stdout.readline()
                if not response:
                    raise RuntimeError("Daemon returned empty response")
                
                return json.loads(response.strip())
            
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON from daemon: {e}")
    
    def stop(self):
        """停止守护进程"""
        if self.process:
            try:
                self.send_command("QUIT")
                self.process.wait(timeout=5)
                print("[INFO] MdDaemon stopped gracefully")
            except Exception as e:
                print(f"[WARN] Error stopping daemon: {e}")
                self.process.terminate()


# 全局守护进程客户端
md_daemon = MdDaemonClient()


# ==================== FastAPI 生命周期 ====================

@app.on_event("startup")
def startup_event():
    """应用启动时初始化守护进程"""
    try:
        md_daemon.start()
        atexit.register(md_daemon.stop)
    except Exception as e:
        print(f"[ERROR] Failed to start MdDaemon: {e}")
        raise


# ==================== API 端点 ====================

@app.get("/health")
def health() -> dict:
    """健康检查"""
    try:
        status = md_daemon.send_command("STATUS")
        return {
            "status": "ok",
            "md_daemon": status,
            "broker_id": os.getenv("CTP_BROKER_ID", ""),
            "md_server": os.getenv("CTP_MD_SERVER", "")
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "broker_id": os.getenv("CTP_BROKER_ID", ""),
            "md_server": os.getenv("CTP_MD_SERVER", "")
        }


@app.get("/md/status")
def md_status() -> dict:
    """获取行情服务状态"""
    try:
        return md_daemon.send_command("STATUS")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to get status: {str(e)}")


@app.get("/md/tick/{instrument_id}")
def get_tick(instrument_id: str) -> dict:
    """
    获取单个合约的行情数据
    - 如果未订阅，会自动订阅
    - 返回最新的 tick 数据
    """
    try:
        # 先尝试直接获取
        result = md_daemon.send_command(f"GET_TICK:{instrument_id}")
        
        if result.get("ok"):
            return result
        
        # 如果没有数据，说明未订阅，先订阅
        error_msg = result.get("error", "").lower()
        if "no data" in error_msg or "not subscribed" in error_msg:
            # 自动订阅
            subscribe_result = md_daemon.send_command(f"SUBSCRIBE:{instrument_id}")
            
            if not subscribe_result.get("ok"):
                raise HTTPException(
                    status_code=502, 
                    detail=f"Failed to subscribe: {subscribe_result.get('error')}"
                )
            
            # 等待数据（最多5秒）
            for i in range(10):
                time.sleep(0.5)
                result = md_daemon.send_command(f"GET_TICK:{instrument_id}")
                
                if result.get("ok"):
                    return result
            
            # 超时仍未获取到数据
            raise HTTPException(
                status_code=504, 
                detail="Timeout waiting for market data after subscription"
            )
        
        raise HTTPException(
            status_code=502, 
            detail=result.get("error", "Failed to get tick data")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {str(e)}")


@app.get("/md/ticks")
def get_ticks_batch(ids: str = Query(..., description="Comma-separated instrument IDs")) -> dict:
    """
    批量查询多个合约的行情数据
    - 自动订阅未订阅的合约
    - 返回成功的数据和失败的错误信息
    
    Example: /md/ticks?ids=CU3M-LME,AL3M-LME,ZN3M-LME
    """
    instrument_ids = [id.strip() for id in ids.split(",") if id.strip()]
    
    if not instrument_ids:
        raise HTTPException(status_code=400, detail="No instrument IDs provided")
    
    if len(instrument_ids) > 50:
        raise HTTPException(status_code=400, detail="Too many instruments (max 50)")
    
    ticks = {}
    errors = {}
    
    for inst_id in instrument_ids:
        try:
            # 尝试获取 tick
            result = md_daemon.send_command(f"GET_TICK:{inst_id}")
            
            if result.get("ok"):
                ticks[inst_id] = result
            else:
                # 未订阅，尝试订阅
                md_daemon.send_command(f"SUBSCRIBE:{inst_id}")
                time.sleep(0.3)  # 短暂等待
                
                result = md_daemon.send_command(f"GET_TICK:{inst_id}")
                if result.get("ok"):
                    ticks[inst_id] = result
                else:
                    errors[inst_id] = result.get("error", "Unknown error")
        
        except Exception as e:
            errors[inst_id] = str(e)
    
    return {
        "ticks": ticks,
        "errors": errors if errors else None
    }


@app.post("/md/subscribe")
def subscribe(payload: dict) -> dict:
    """
    明确订阅合约（持久订阅）
    
    Request body:
    {
        "instrument_ids": ["CU3M-LME", "AL3M-LME"]
    }
    """
    instrument_ids = payload.get("instrument_ids", [])
    
    if not isinstance(instrument_ids, list) or not instrument_ids:
        raise HTTPException(status_code=400, detail="instrument_ids must be a non-empty list")
    
    subscribed = []
    failed = {}
    
    for inst_id in instrument_ids:
        try:
            result = md_daemon.send_command(f"SUBSCRIBE:{inst_id}")
            if result.get("ok"):
                subscribed.append(inst_id)
            else:
                failed[inst_id] = result.get("error", "Unknown error")
        except Exception as e:
            failed[inst_id] = str(e)
    
    return {
        "ok": True,
        "subscribed": subscribed,
        "failed": failed if failed else None
    }


@app.post("/md/unsubscribe")
def unsubscribe(payload: dict) -> dict:
    """
    取消订阅合约
    
    Request body:
    {
        "instrument_ids": ["CU3M-LME"]
    }
    """
    instrument_ids = payload.get("instrument_ids", [])
    
    if not isinstance(instrument_ids, list) or not instrument_ids:
        raise HTTPException(status_code=400, detail="instrument_ids must be a non-empty list")
    
    unsubscribed = []
    failed = {}
    
    for inst_id in instrument_ids:
        try:
            result = md_daemon.send_command(f"UNSUBSCRIBE:{inst_id}")
            if result.get("ok"):
                unsubscribed.append(inst_id)
            else:
                failed[inst_id] = result.get("error", "Unknown error")
        except Exception as e:
            failed[inst_id] = str(e)
    
    return {
        "ok": True,
        "unsubscribed": unsubscribed,
        "failed": failed if failed else None
    }


# ==================== 合约查询（TraderApi）====================

@app.get("/instruments")
def list_instruments(
    exchange: Optional[str] = Query(None, description="Filter by exchange (e.g., CME, ICE, LME)"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., metal, energy, agriculture)")
) -> dict:
    """
    查询所有可用合约
    
    参数：
    - exchange: 交易所代码（CME, ICE, LME, NYMEX, CBOT, COMEX 等）
    - category: 品种类别（自动识别：metal, energy, agriculture 等）
    
    示例：
    - /instruments - 返回所有合约
    - /instruments?exchange=CME - 只返回 CME 的合约
    - /instruments?exchange=LME - 只返回 LME（伦敦金属）的合约
    """
    front = os.getenv("CTP_TRADE_SERVER") or ""
    broker = os.getenv("CTP_BROKER_ID") or ""
    user = os.getenv("CTP_USER_ID") or ""
    password = os.getenv("CTP_PASSWORD") or ""
    
    if not all([front, broker, user, password]):
        raise HTTPException(status_code=400, detail="Missing CTP credentials")
    
    try:
        result = subprocess.run(
            ["/usr/local/bin/td_query_instruments", front, broker, user, password],
            capture_output=True,
            text=True,
            timeout=120,
            env={"LD_LIBRARY_PATH": "/usr/local/lib/ctp"}
        )
        
        if not result.stdout:
            return {"ok": False, "stderr": result.stderr.strip()}
        
        data = json.loads(result.stdout.strip())
        
        if not data.get("ok"):
            return data
        
        instruments = data.get("instruments", [])
        
        # 按交易所分组
        by_exchange = {}
        for inst in instruments:
            # 提取交易所代码（假设格式为 XXX-EXCHANGE 或 O_XXX-EXCHANGE）
            parts = inst.split("-")
            if len(parts) >= 2:
                exch = parts[-1]  # 最后一部分是交易所
                if exch not in by_exchange:
                    by_exchange[exch] = []
                by_exchange[exch].append(inst)
        
        # 如果指定了交易所，只返回该交易所的合约
        if exchange:
            exchange_upper = exchange.upper()
            filtered = by_exchange.get(exchange_upper, [])
            return {
                "ok": True,
                "exchange": exchange_upper,
                "count": len(filtered),
                "instruments": filtered
            }
        
        # 返回完整数据
        return {
            "ok": True,
            "total_count": len(instruments),
            "exchanges": list(by_exchange.keys()),
            "by_exchange": {k: {"count": len(v), "instruments": v} for k, v in by_exchange.items()},
            "instruments": instruments
        }
    
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Query instruments error: {e}")


# ==================== 测试端点 ====================

@app.get("/md/login-test")
def md_login_test() -> dict:
    """测试 MdApi 登录（使用一次性工具）"""
    front = os.getenv("CTP_MD_SERVER") or ""
    broker = os.getenv("CTP_BROKER_ID") or ""
    user = os.getenv("CTP_USER_ID") or ""
    password = os.getenv("CTP_PASSWORD") or ""
    
    if not all([front, broker, user, password]):
        raise HTTPException(status_code=400, detail="Missing CTP credentials")
    
    try:
        result = subprocess.run(
            ["/usr/local/bin/md_login", front, broker, user, password],
            capture_output=True,
            text=True,
            timeout=40,
            env={"LD_LIBRARY_PATH": "/usr/local/lib/ctp"}
        )
        
        if result.stdout:
            return json.loads(result.stdout.strip())
        
        return {"ok": False, "stderr": result.stderr.strip()}
    
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Login test error: {e}")
