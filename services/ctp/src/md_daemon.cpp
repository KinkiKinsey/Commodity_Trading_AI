#include "ThostFtdcMdApi.h"
#include <iostream>
#include <string>
#include <map>
#include <set>
#include <mutex>
#include <thread>
#include <chrono>
#include <cstring>
#include <atomic>

// 简单的 JSON 工具函数
std::string escapeJson(const std::string& str) {
    std::string result;
    for (char c : str) {
        if (c == '"') result += "\\\"";
        else if (c == '\\') result += "\\\\";
        else result += c;
    }
    return result;
}

class MdDaemon : public CThostFtdcMdSpi {
private:
    CThostFtdcMdApi* api;
    std::string broker_id;
    std::string user_id;
    std::string password;
    std::string front_addr;  // 保存前置地址
    
    std::atomic<bool> logged_in{false};
    std::atomic<bool> running{true};
    
    // Tick 数据缓存
    std::map<std::string, CThostFtdcDepthMarketDataField> tick_cache;
    std::mutex cache_mutex;
    
    // 订阅列表
    std::set<std::string> subscribed_instruments;
    std::mutex subscribe_mutex;

public:
    MdDaemon(const std::string& front, const std::string& broker, 
             const std::string& user, const std::string& pwd)
        : broker_id(broker), user_id(user), password(pwd), front_addr(front) {
        
        // 创建 flow 文件目录
        system("mkdir -p /tmp/md_daemon && rm -rf /tmp/md_daemon/*");
        
        // 创建 API 实例
        api = CThostFtdcMdApi::CreateFtdcMdApi("/tmp/md_daemon/");
        api->RegisterSpi(this);
        api->RegisterFront(const_cast<char*>(front_addr.c_str()));
        
        std::cerr << "[INFO] MdDaemon initializing..." << std::endl;
        std::cerr << "[INFO] Connecting to: " << front_addr << std::endl;
        api->Init();
    }
    
    ~MdDaemon() {
        if (api) {
            api->RegisterSpi(nullptr);
            api->Release();
        }
    }
    
    // ==================== CTP 回调 ====================
    
    void OnFrontConnected() override {
        std::cerr << "[INFO] Front connected, logging in..." << std::endl;
        
        CThostFtdcReqUserLoginField req = {};
        strncpy(req.BrokerID, broker_id.c_str(), sizeof(req.BrokerID) - 1);
        strncpy(req.UserID, user_id.c_str(), sizeof(req.UserID) - 1);
        strncpy(req.Password, password.c_str(), sizeof(req.Password) - 1);
        
        api->ReqUserLogin(&req, 1);
    }
    
    void OnFrontDisconnected(int reason) override {
        logged_in = false;
        std::cerr << "[WARN] Front disconnected, reason: " << reason << std::endl;
        std::cerr << "[INFO] Will auto-reconnect..." << std::endl;
    }
    
    void OnRspUserLogin(CThostFtdcRspUserLoginField* login,
                        CThostFtdcRspInfoField* info,
                        int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            std::cerr << "[ERROR] Login failed: " << info->ErrorID 
                      << " - " << info->ErrorMsg << std::endl;
            return;
        }
        
        logged_in = true;
        std::cerr << "[INFO] Login successful! TradingDay: " 
                  << (login ? login->TradingDay : "unknown") << std::endl;
        std::cerr << "[INFO] Daemon ready for commands." << std::endl;
    }
    
    void OnRspSubMarketData(CThostFtdcSpecificInstrumentField* inst,
                           CThostFtdcRspInfoField* info,
                           int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            std::cerr << "[ERROR] Subscribe failed: " << info->ErrorID 
                      << " - " << info->ErrorMsg << std::endl;
            return;
        }
        
        if (inst) {
            std::lock_guard<std::mutex> lock(subscribe_mutex);
            subscribed_instruments.insert(inst->InstrumentID);
            std::cerr << "[INFO] Subscribed: " << inst->InstrumentID << std::endl;
        }
    }
    
    void OnRspUnSubMarketData(CThostFtdcSpecificInstrumentField* inst,
                             CThostFtdcRspInfoField* info,
                             int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            std::cerr << "[ERROR] Unsubscribe failed: " << info->ErrorID 
                      << " - " << info->ErrorMsg << std::endl;
            return;
        }
        
        if (inst) {
            std::lock_guard<std::mutex> lock(subscribe_mutex);
            subscribed_instruments.erase(inst->InstrumentID);
            std::cerr << "[INFO] Unsubscribed: " << inst->InstrumentID << std::endl;
        }
    }
    
    void OnRtnDepthMarketData(CThostFtdcDepthMarketDataField* data) override {
        if (!data) return;
        
        std::lock_guard<std::mutex> lock(cache_mutex);
        tick_cache[data->InstrumentID] = *data;
    }
    
    // ==================== 命令处理 ====================
    
    void ProcessCommand(const std::string& line) {
        if (line.empty()) return;
        
        if (line == "QUIT") {
            running = false;
            std::cout << "{\"ok\":true,\"message\":\"Daemon stopping\"}" << std::endl;
        }
        else if (line == "STATUS") {
            HandleStatus();
        }
        else if (line.find("SUBSCRIBE:") == 0) {
            std::string instrument_id = line.substr(10);
            HandleSubscribe(instrument_id);
        }
        else if (line.find("UNSUBSCRIBE:") == 0) {
            std::string instrument_id = line.substr(12);
            HandleUnsubscribe(instrument_id);
        }
        else if (line.find("GET_TICK:") == 0) {
            std::string instrument_id = line.substr(9);
            HandleGetTick(instrument_id);
        }
        else if (line == "PING") {
            std::cout << "{\"ok\":true,\"pong\":true}" << std::endl;
        }
        else {
            std::cout << "{\"ok\":false,\"error\":\"Unknown command\"}" << std::endl;
        }
    }
    
    void HandleStatus() {
        std::lock_guard<std::mutex> lock(subscribe_mutex);
        
        std::cout << "{\"ok\":true,\"logged_in\":" 
                  << (logged_in ? "true" : "false")
                  << ",\"subscribed_count\":" << subscribed_instruments.size()
                  << ",\"cached_count\":" << tick_cache.size()
                  << ",\"subscribed\":[";
        
        bool first = true;
        for (const auto& inst : subscribed_instruments) {
            if (!first) std::cout << ",";
            std::cout << "\"" << escapeJson(inst) << "\"";
            first = false;
        }
        
        std::cout << "]}" << std::endl;
    }
    
    void HandleSubscribe(const std::string& instrument_id) {
        if (!logged_in) {
            std::cout << "{\"ok\":false,\"error\":\"Not logged in\"}" << std::endl;
            return;
        }
        
        // 检查是否已订阅
        {
            std::lock_guard<std::mutex> lock(subscribe_mutex);
            if (subscribed_instruments.count(instrument_id)) {
                std::cout << "{\"ok\":true,\"already_subscribed\":true}" << std::endl;
                return;
            }
        }
        
        // 订阅
        char* ids[] = {const_cast<char*>(instrument_id.c_str())};
        int ret = api->SubscribeMarketData(ids, 1);
        
        if (ret != 0) {
            std::cout << "{\"ok\":false,\"error\":\"Subscribe request failed\"}" << std::endl;
            return;
        }
        
        // 等待首次数据（最多5秒）
        for (int i = 0; i < 50; i++) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
            std::lock_guard<std::mutex> lock(cache_mutex);
            if (tick_cache.count(instrument_id)) {
                std::cout << "{\"ok\":true,\"subscribed\":true,\"got_data\":true}" << std::endl;
                return;
            }
        }
        
        std::cout << "{\"ok\":true,\"subscribed\":true,\"got_data\":false}" << std::endl;
    }
    
    void HandleUnsubscribe(const std::string& instrument_id) {
        if (!logged_in) {
            std::cout << "{\"ok\":false,\"error\":\"Not logged in\"}" << std::endl;
            return;
        }
        
        char* ids[] = {const_cast<char*>(instrument_id.c_str())};
        int ret = api->UnSubscribeMarketData(ids, 1);
        
        if (ret != 0) {
            std::cout << "{\"ok\":false,\"error\":\"Unsubscribe request failed\"}" << std::endl;
            return;
        }
        
        // 清除缓存
        {
            std::lock_guard<std::mutex> lock(cache_mutex);
            tick_cache.erase(instrument_id);
        }
        
        std::cout << "{\"ok\":true,\"unsubscribed\":true}" << std::endl;
    }
    
    void HandleGetTick(const std::string& instrument_id) {
        std::lock_guard<std::mutex> lock(cache_mutex);
        
        auto it = tick_cache.find(instrument_id);
        if (it == tick_cache.end()) {
            std::cout << "{\"ok\":false,\"error\":\"No data (not subscribed?)\"}" << std::endl;
            return;
        }
        
        const auto& data = it->second;
        
        std::cout << "{\"ok\":true"
                  << ",\"instrument_id\":\"" << escapeJson(data.InstrumentID) << "\""
                  << ",\"last_price\":" << data.LastPrice
                  << ",\"volume\":" << data.Volume
                  << ",\"trading_day\":\"" << escapeJson(data.TradingDay) << "\""
                  << ",\"update_time\":\"" << escapeJson(data.UpdateTime) << "\""
                  << ",\"update_millisec\":" << data.UpdateMillisec
                  << ",\"bid_price1\":" << data.BidPrice1
                  << ",\"bid_volume1\":" << data.BidVolume1
                  << ",\"ask_price1\":" << data.AskPrice1
                  << ",\"ask_volume1\":" << data.AskVolume1
                  << "}" << std::endl;
    }
    
    // ==================== 主循环 ====================
    
    void Run() {
        std::cerr << "[INFO] Daemon running, waiting for commands..." << std::endl;
        std::cerr << "[INFO] Available commands: STATUS, SUBSCRIBE:<id>, UNSUBSCRIBE:<id>, GET_TICK:<id>, PING, QUIT" << std::endl;
        
        std::string line;
        while (running && std::getline(std::cin, line)) {
            // 移除末尾空白字符
            while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) {
                line.pop_back();
            }
            
            ProcessCommand(line);
            std::cout.flush();
        }
        
        std::cerr << "[INFO] Daemon shutting down..." << std::endl;
    }
};

int main(int argc, char* argv[]) {
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0] 
                  << " <front> <broker_id> <user_id> <password>" << std::endl;
        return 1;
    }
    
    std::string front = argv[1];
    std::string broker = argv[2];
    std::string user = argv[3];
    std::string password = argv[4];
    
    try {
        MdDaemon daemon(front, broker, user, password);
        
        // 等待登录成功
        std::this_thread::sleep_for(std::chrono::seconds(3));
        
        daemon.Run();
    }
    catch (const std::exception& e) {
        std::cerr << "[FATAL] Exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}

