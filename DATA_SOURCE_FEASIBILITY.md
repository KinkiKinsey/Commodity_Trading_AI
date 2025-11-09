# CTP 瀹炴椂 K 绾挎柟妗堬紙鏁版嵁婧愬彲琛屾€т笌瀹炴柦璁″垝锛?

> 鐩爣锛氫互 CTP 鎻愪緵鐨勮鎯呮暟鎹负鏍稿績锛屾瀯寤轰竴濂楀熀浜?TradingView lightweight鈥慶harts 鐨勫疄鏃?K 绾跨郴缁燂紝绋冲畾灞曠ず鏈€鏂?6 涓悎绾︼紙CL2512銆丆L2601鈥慍L2605锛夈€傛柟妗堥渶鍏奸【鎸囨爣鍙犲姞銆佸懆鏈熷垏鎹€佺郴鍒楁瘮杈冦€丷ingshell 姘村嵃銆佷俊鍙疯仈鍔ㄧ瓑涓€绯诲垪澧炲己鍔熻兘銆?

---

## 1. 鏁版嵁娴佷笌瀛樺偍

| 妯″潡 | 鐜扮姸 | 鏀归€犳柟妗?|
| --- | --- | --- |
| **CTP Tick 鎷夊彇** | 浠呮湁 `/md/tick/{instrument_id}` 鍗曠瑪鎺ュ彛 | 鏂板缓鍚庡彴 Aggregator锛氬懆鏈熸€э紙鈮?s锛夎闂?`/md/ticks?ids=...`锛堝彲鎵归噺锛夊苟鍐欏叆缂撳瓨 + 闃熷垪锛涘鎵归噺鎺ュ彛涓嶅瓨鍦紝鍒欏绾跨▼涓茶璇锋眰鍚庡悎骞?|
| **鍚堢害绐楀彛** | 6 涓?CL 鍚堢害鎵嬪姩閰嶇疆 | 閫氳繃 `generateContractIds()` 瀹炴椂鐢熸垚 `n=12` 鐨勫€欓€夊垪琛紱杩囨护宸茶繃鏈熷悎绾︼紝淇濊瘉鍓嶇鎬昏兘鍙栧埌 6 鏉℃渶鏂?|
| **鍘嗗彶 OHLC** | AlphaVantage 鏃ョ嚎 | 鍚庣鏂板 `bar_builder`锛氫互 tick 娴佷负杈撳叆锛岀敓鎴?1m/5m/15m/1h/1d bar锛圞afka/Redis 浜嬩欢 + Postgres/ClickHouse 瀛樺偍锛夛紱鑻ョ煭鏈熸棤娉曡惤搴擄紝鍙湪鍐呭瓨涓淮鎶ゆ渶杩?N 鍒嗛挓 bar锛屽苟鍛ㄦ湡钀界洏 |
| **鎸囨爣/淇″彿** | ML 鍧囩嚎銆佸竷鏋楃瓑渚濊禆鍘嗗彶鏁版嵁 | 瑙ｆ瀽 `INDEX1.xlsx` 涓烘寚鏍囬厤缃紙JSON/CSV锛夛紝鍚庡彴瀹氭椂璁＄畻/缂撳瓨锛涜緭鍑虹粺涓€ `indicatorSeries`锛坱imestamp,value锛?|
| **API** | `/api/pricing/kline` 杩斿洖 Alpha 鏁版嵁 | 鏂板 `/api/ctp/kline`锛氳繑鍥?bar 鏁版嵁 + 鎸囨爣 + 瀹炴椂淇″彿锛涗繚鎸佸瓧娈典笌鍓嶇绫诲瀷鍏煎锛屼究浜庢笎杩涜縼绉?|

### 鏁版嵁缁撴瀯绀轰緥
```jsonc
{
  "symbol": "CL2512-NYM",
  "bars": [{ "time": 1731042000, "open": 78.1, "high": 79.2, "low": 77.8, "close": 78.76, "volume": 12039 }],
  "indicators": {
    "ml_ma": [{ "time": 1731042000, "value": 77.3 }],
    "boll_upper": [],
    "...": []
  },
  "signals": [
    { "time": 1731042300, "type": "bearish", "confidence": 0.78, "text": "BEARISH trend..." }
  ],
  "realtime": {
    "bid": 78.70,
    "bidSize": 12,
    "ask": 78.80,
    "askSize": 15,
    "last": 78.76,
    "lastUpdate": "2025-11-08T11:40:00Z"
  }
}
```

### 1.1 瀹炴椂鍒锋柊楠岃瘉

涓虹‘璁?`md/tick` 鐨勫埛鏂伴鐜囷紝鏂板閲囨牱鑴氭湰 `scripts/ctp_tick_probe.py`锛屼互 1 绉掑懆鏈熸姄鍙?6 娆★細

```bash
python scripts/ctp_tick_probe.py CL2512-NYM 6 1
```

杈撳嚭绀轰緥锛?

```
{'local_time': '20:09:13', 'update_time': '06:00:00', 'update_millisec': 830, 'last_price': 59.84}
...
20:09:17 -> update 06:00:00.830 price 59.84
```

**缁撹**锛氭帴鍙ｅ彲琚珮棰戣闂紝浣嗗湪鏃犳垚浜ゅ彉鍖栨椂杩斿洖鍚屼竴绗旓紙`update_time` 鏈彉锛夈€傚洜姝わ細

1. 浠嶉渶鎸?鈮? 绉掗鐜囬噰闆嗭紝纭繚浠讳綍璺冲彉閮借璁板綍锛?
2. 閲囬泦鍣ㄩ渶灏?`local_time` 涓?`update_time` 鍚屾椂钀藉簱锛屾柟渚垮悗缁垎鏋愬欢杩燂紱
3. 涓?CTP 渚涘簲鍟嗙‘璁ゆ槸鍚︽彁渚涙帹閫佸紡鎺ュ彛锛圵ebSocket锛変互鍑忚交杞鍘嬪姏銆?

---

## 2. 鍓嶇鎬讳綋缁撴瀯

### 2.1 鐘舵€佺鐞?
- `contractsStore`锛圸ustand锛夛細缁存姢鏈€鏂?6 涓悎绾︺€佸墠涓€鐗堟湰 tick銆佹洿鏂扮姸鎬併€?
- `chartStore`: 璁板綍褰撳墠鍚堢害銆佹瘮杈冪郴鍒椼€佸懆鏈熴€佹寚鏍囧紑鍏炽€佷俊鍙疯繃婊ょ瓑銆?
- React Query 瀵?`/api/ctp/kline`銆乣/api/ctp/realtime` 鍋氳疆璇笌缂撳瓨锛屽厑璁?fall鈥慴ack 鍒版渶鍚庢垚鍔熷€笺€?

### 2.2 缁勪欢鍒掑垎
| 缁勪欢 | 璇存槑 |
| --- | --- |
| `CtpRealtimePanel` | 宸︿晶鍗＄墖锛屽睍绀?6 涓悎绾︾殑 tick 淇℃伅锛堝凡鍦ㄧ幇鏈夐〉闈㈠疄鐜帮紝鍙户缁凯浠ｏ級 |
| `ChartShell` | 瀵?lightweight-charts 鍋氱粺涓€灏佽锛氫富棰樸€佸昂瀵稿搷搴斿紡銆丷ingshell 姘村嵃銆乼ooltip銆佽嚜瀹氫箟鍥惧眰锛?*鏀剧疆浣嶇疆锛氭柊闂诲疄鏃堕〉鐜版湁 TradingView 鍖哄潡涓嬫柟銆佺煶娌瑰洜瀛愭ā鍧椾笂鏂?*锛?|
| `CtpKline` | 璋冪敤 ChartShell 娓叉煋涓?K 绾裤€佹瘮杈冪嚎銆佹寚鏍囩嚎銆佷俊鍙锋爣璁扮瓑锛涘寘鍚伐鍏锋爮锛堝懆鏈熴€佹寚鏍囥€佹瘮杈冦€佸鍑虹瓑锛?|
| `IndicatorPanel` | 瑙ｆ瀽 INDEX1 鎸囨爣閰嶇疆锛屾彁渚涘紑鍏炽€佹牱寮忚缃紙棰滆壊銆丳ane锛?|
| `SignalTimeline` | 鍥惧舰涓嬫柟鍒楀嚭淇″彿鍒楄〃锛岀偣鍑诲彲瀹氫綅鍒?chart marker |

### 2.3 TradingView lightweight鈥慶harts 闆嗘垚
1. 灏?`C:\Users\juiceNo3\Downloads\lightweight-charts-master` 寮曞叆 workspace锛堝 `frontend/web/libs/lightweight-charts`锛夈€?
2. 鍦?`ChartShell` 涓?`import { createChart } from "@/libs/lightweight-charts"`銆?
3. 鑷畾涔変富棰橈細鑳屾櫙銆佺綉鏍笺€佸埢搴︺€佸崄瀛楃嚎銆乼ooltip 鍧囦娇鐢?Ringshell 鐨勪腑鎬ч厤鑹层€?
4. Watermark锛氬湪 `chart.subscribeCrosshairMove` 鎴?`applyOptions` 涓紝鍒╃敤 `paneWidget` 鐢昏嚜瀹氫箟 canvas锛坄Ringshell 鈥?AI Markets`锛夈€?
5. 鍏佽娣诲姞澶?`series`锛歚candlestickSeries`銆乣baselineSeries`锛堟瘮杈冿級銆乣lineSeries`锛堟寚鏍囷級銆乣histogram`锛堟垚浜ゆ祦锛夈€乣series.createPriceLine`锛堝熀鍑嗙嚎锛夈€?

---

## 3. 鎸囨爣涓庝俊鍙凤紙INDEX1.xlsx锛?

1. **棰勫鐞?*锛氬悗绔?cron 璇诲彇 `INDEX1.xlsx`锛岃浆鎹负 JSON锛歚[{symbol, timestamp, indicatorKey, value}]`銆?
2. **娉ㄥ唽绯荤粺**锛?
   ```ts
   const indicatorRegistry = {
     ml_ma: { label: "ML 鍧囩嚎", type: "line", color: "#5B8FF9" },
     boll_upper: { label: "Boll 涓婅建", type: "line", color: "#FF7875" },
     spread_score: { label: "浠峰樊寰楀垎", type: "histogram", pane: "lower" },
     ...
   };
   ```
3. **娓叉煋閫昏緫**锛氱敤鎴峰嬀閫?-> `ChartShell` 鏍规嵁 type/pane 娣诲姞 series锛涙寚鏍囧€奸殢 `/api/ctp/kline` 杩斿洖銆?
4. **淇″彿鑱斿姩**锛歚signals` 鏁扮粍杞负 `chartSeries.setMarkers()` 骞跺湪 SignalTimeline 涓垪鍑恒€傜偣鍑?marker 鍙墦寮€ Tooltip/Drawer 灞曠ず璇︾粏 AI 缁撹銆佺疆淇″害绛夈€?

---

## 4. 鍔熻兘鍒楄〃

| 鍔熻兘 | 鎻忚堪 |
| --- | --- |
| 鍛ㄦ湡鍒囨崲鍣?| 鏀寔 1m/5m/15m/1h/1d锛屽垏鎹㈡椂閲嶆柊璇锋眰 `/api/ctp/kline?interval=` |
| 绯诲垪姣旇緝 | 鍦ㄥ伐鍏锋爮閫夋嫨鍏朵粬鍚堢害锛屾坊鍔?baseline/line 绯诲垪骞跺悓姝?legend |
| 鍥介檯鍖?| labels 澶嶇敤 `IntlContext`锛屼腑鏂?鑻辨枃瀵规槧瀹屾暣 |
| 淇″彿杩囨护 | 鎸夌被鍨?缃俊搴﹁繃婊?marker锛涘嬀閫夆€滀粎鏄剧ず AI 缁撹/浠呮樉绀虹爺鍒も€?|
| 鑷姩鍒锋柊 | 鏄剧ず 鈥滀笂娆℃洿鏂帮紙xx:xx锛?路 姝ｅ湪鍒锋柊/澶辫触鈥?骞跺厑璁告墜鍔ㄥ埛鏂版垨鏆傚仠 |
| 鎴浘瀵煎嚭 | 浣跨敤 `chart.takeScreenshot()` 鎴?`html2canvas` 杈撳嚭 PNG |
| 蹇嵎閿?| 鏂瑰悜閿垏鎹㈠悎绾?鍛ㄦ湡锛宍F` 鑱氱劍鏈€鏂帮紝鎻愬崌鎿嶆帶鏁堢巼 |
| 鎬ц兘浼樺寲 | 浣跨敤 `requestAnimationFrame` 鍘绘姈 resize锛岀紦瀛?500 鏍逛互鍐呮暟鎹紝瓒呭嚭鏃惰鍓?|

---

## 5. 瀹炴柦姝ラ锛堢粏鍖栵級

### Phase A 路 鏁版嵁閲囬泦涓?API锛堥璁?3 澶╋級
1. 鉁?`ctp_sampler` Daemon锛歚scripts/ctp_collector.py` 宸插疄鐜帮紙鏀寔鍔ㄦ€佸悎绾︺€?s 杞銆佸け璐ュ憡璀︺€並afka/CSV 杈撳嚭銆乣--dry-run/--max-cycles` 璋冭瘯鍙傛暟锛夈€傚悗缁彲鐩存帴鐢ㄤ簬 Docker 閮ㄧ讲鎴栨帴 Kafka銆?
2. 鉁?Docker 鍩虹鐜锛氭柊澧?`Dockerfile.collector` 涓?`docker-compose.ctp.yml`锛屾湰鍦颁竴鏉″懡浠ゅ嵆鍙惎鍔?`zookeeper + kafka + clickhouse + collector`锛涘噯澶囧ソ涓庣敓浜х幆澧冧竴鑷寸殑缂栨帓妯℃澘銆?
3. 鉁?Kafka 鍐欏叆閾捐矾锛歝ollector 浠?6 鍚堢害绐楀彛姣忕鎺ㄩ€?`ctp_ticks` topic锛屽苟闄勫甫 `local_time / update_time / bid/ask/last` 瀛楁锛涢€氳繃 `docker compose -f docker-compose.ctp.yml exec kafka kafka-console-consumer ...` 宸查獙璇佹秷鎭寔缁骇鍑猴紝鎶ヨ閫昏緫涔熷湪鑴氭湰鍐呰褰曡繛缁け璐ャ€?
4. 鉁?ClickHouse 鍒濆鍖?+ 娑堣垂锛歚scripts/clickhouse_init.sql` 宸插湪瀹瑰櫒鍐呮墽琛屽畬姣曪紝`scripts/kafka_to_clickhouse.py` 鐜拌繍琛屼簬 compose 缃戠粶涓紝`ctp.ctp_ticks` 琛屾暟鎸佺画澧炲姞锛岃瘉鏄?Kafka鈫扖lickHouse 鍐欏叆闂幆鍙敤銆?
5. 璁捐 `ctp_bars_<interval>` 鐗╁寲瑙嗗浘锛氭寜 1m/5m/15m/1h/1d 鑱氬悎 OHLCV锛屼緵 `/api/ctp/kline` 鐩存帴鏌ヨ锛涘鍘嗗彶涓嶈冻鍙厛杩斿洖 mock 鏁版嵁銆?

### Phase B 路 ChartShell & 鍓嶇鍩虹锛堥璁?4 澶╋級
1. 鉁?`ChartShell` 灏佽瀹屾垚锛氬熀浜庢湰鍦?lightweight-charts 婧愮爜瀹炵幇涓婚銆丷ingshell 姘村嵃銆佸搷搴斿紡銆乵arkers/澶?series 鍙婂鍑?API锛屼緵鍚庣画 K 绾跨粍浠剁粺涓€璋冪敤銆?
2. 鉁?`CtpKlineCard`锛坢ock 鏁版嵁锛夊凡鍦ㄦ柊闂诲疄鏃堕〉 **TradingView 鍥惧潡涓嬫柟銆佺煶娌瑰洜瀛愪笂鏂?* 娓叉煋锛岄粯璁ゆ彁渚涘懆鏈?鍚堢害鍒囨崲锛屽苟涓?TradingView 骞跺瓨锛岀瓑寰呯湡瀹?`/api/ctp/kline` 鏁版嵁鎺ュ叆銆?
3. 鉁?宸ュ叿鏍忓寮猴細鏂伴椈椤典腑鐨?`CtpKlineCard` 鐜板寘鍚懆鏈?鍚堢害鍒囨崲銆佹渶鍚庢洿鏂版椂闂淬€佹墜鍔?+ 15s 鑷姩鍒锋柊鐘舵€侊紝鏂逛究鍦ㄦ帴鍏ョ湡鏁版嵁鍓嶉獙璇佷氦浜掞紱ChartShell 宸查獙璇佸彲鍚屾椂缁樺埗 K 绾?+ 鍙犲姞绾裤€?

### Phase C 路 鍚庣 API锛堥璁?3 澶╋級
1. 鉁?`/api/ctp/kline` 宸蹭笂绾匡細FastAPI 璋冪敤 ClickHouse HTTP 鎺ュ彛璇诲彇 `ctp_bars_1m`锛屾敮鎸?1m/5m/15m/1h interval銆乧ount/绗﹀彿鏍￠獙锛岃繑鍥?`PriceBar + RangeMetadata` 缁撴瀯骞跺甫寤惰繜鍏冩暟鎹€?
2. 鉁?`/api/ctp/realtime`锛欶astAPI 鐩磋繛 ClickHouse 鏈€鏂?tick锛堝惈 bid/ask/volume/寤惰繜鍏冩暟鎹級锛屼緵宸︿晶 tick 闈㈡澘涓?ChartShell tooltip 鍏辩敤銆?
3. 鉁?ClickHouse 缂撳瓨/鍋ュ悍妫€鏌ワ細`/api/ctp/realtime` 鍐呯疆 1s TTL + 鏈€灏忔姄鍙栭棿闅旓紝澶辫触鍥炶惤鍒颁笂娆＄紦瀛橈紱鏂板 `/api/ctp/healthz`锛岃繑鍥炶〃琛屾暟涓庢渶鏂版椂闂存埑锛屼究浜庣洃鎺с€?

### Phase D 路 鍓嶇闆嗘垚锛堥璁?4 澶╋級
1. 鉁?`useCtpKline` hook 宸插疄鐜板苟鎺ュ叆 `CtpKlineCard`锛屾敮鎸?interval/count/閿欒鍥為€€銆?
2. 鏂扮殑 ChartShell锛坙ightweight-charts锛夊湪鎸囧畾浣嶇疆鏂板锛屼笌 TradingView 骞跺瓨锛岄檮 Ringshell 姘村嵃銆佷俊鍙?marker銆佹寚鏍囧彔鍔犮€佸鍑哄伐鍏凤紱`CtpKlineCard` 宸茶鍙栧疄鏃?tick 骞跺睍绀哄欢杩熴€?
3. 渚ф爮/宸ュ叿鏍忥細瀹炵幇鍛ㄦ湡鍒囨崲鍣ㄣ€佸悎绾︽瘮杈冦€佹寚鏍囬潰鏉裤€佷俊鍙疯繃婊ゃ€佽嚜鍔ㄥ埛鏂版彁绀虹瓑浜や簰銆?

### Phase E 路 鎸囨爣/淇″彿锛堥璁?3 澶╋級
1. 瑙ｆ瀽 `INDEX1.xlsx` 鈫?JSON 鈫?瀹氭椂鍐欏叆 ClickHouse `ctp_indicators` 琛ㄣ€?
2. `/api/ctp/kline` 杩斿洖鎸囨爣鏁版嵁锛涘墠绔?IndicatorPanel 鎺у埗鏄剧ず/闅愯棌銆?
2a. ✅ scripts/backfill_indicator_series.py �� ClickHouse CLICKHOUSE_HTTP_URL �Խ����� ctp.ctp_indicator_series ���怡���룬��� API ���Ի���ʵ����
3. ✅ ��ʾ marker �� SignalTimeline ����������ɶ�λ��CtpSignalTimeline �� ChartShell markers �ѽ��� MLMA ����֮�źš�

### Phase F 路 娴嬭瘯涓庝笂绾匡紙棰勮 3 澶╋級
1. 鍗曞厓娴嬭瘯锛欿afka/ClickHouse 鍐欏叆閾捐矾銆丄PI 杈撳嚭銆佸墠绔?hooks & 缁勪欢 snapshot銆?
1. ✅ 脚本/单元验证：`python -m compileall backend/src`、`npm run lint`、`scripts/check_clickhouse.py` 确认 Kafka→ClickHouse→API→前端链路可用。
2. ✅ `scripts/diagnose_docker.ps1` + `diagnose_full.ps1` 检查容器状态、端口连通性与 ClickHouse 样本，collector 3s 周期满足性能需求。
3. ✅ `docker compose -f docker-compose.ctp.yml up -d` 灰度重启 + `.env` 切换 18123 端口已完成，AlphaVantage 保留为 fallback。
### DevOps & 閮ㄧ讲澶囨敞
- 鏈湴涓庢湇鍔″櫒缁熶竴閫氳繃 `docker compose -f docker-compose.ctp.yml up -d` 鍚姩 `zookeeper + kafka + clickhouse + collector + kafka_to_clickhouse`锛岀‘淇濆紑鍙?/ 娴嬭瘯 / 绾夸笂鐜涓€鑷达紱蹇呰鏃惰剼鏈ā寮忎粎浣滃崟娆¤瘖鏂娇鐢ㄣ€?
- `Dockerfile.collector` 鐩存帴灏佽瀹堟姢杩涚▼锛坧ython:3.10-slim + requirements锛夛紝鍚庣画涓婄嚎鍙皢鍚屼竴闀滃儚鎸傚叆 Compose/Swarm/K8s锛屽苟浣跨敤 `.env` 绠＄悊 CTP/Kafka/ClickHouse 鐨勫湴鍧€涓庡嚟璇併€?
- CTP 鏈嶅姟宸查儴缃插湪澶栭儴鏈嶅姟鍣紝缁忚剼鏈笌瀹瑰櫒鍙岄噸楠岃瘉鍙ǔ瀹氳繛鎺ワ紱鍦?Docker 鐜鍙渶閰嶇疆姝ｇ‘ URL/Key锛屽嵆鍙暱鏈熼噰闆嗐€?

--- 

## 6. 椋庨櫓 & 瀵圭瓥

| 椋庨櫓 | 璇存槑 | 瀵圭瓥 |
| --- | --- | --- |
| CTP 鎺ュ彛涓嶅彲鐢?| 鏃犲巻鍙层€佹棤鎵归噺 | 鍚庣鏈湴钀藉簱 + 缂撳瓨锛涘繀瑕佹椂鍔犲叆绗笁鏂瑰鐢ㄦ暟鎹簮 |
| 鎸囨爣璁＄畻鎴愭湰楂?| Excel 鍒楄〃涓嶆柇鎵╁厖 | 瀹氭湡鎵瑰鐞?+ 缂撳瓨锛屽繀瑕佹椂鎷嗗垎寰湇鍔?|
| TradingView 閫傞厤宸紓 | 鏈湴 lightweight-charts 鐗堟湰闇€鍗囩骇 | 浠庡畼鏂?repo 寮曞叆鏈€鏂扮増鏈紝骞剁紪鍐欏皝瑁呴槻姝?breaking changes |
| UI/鎬ц兘 | 澶?series 鍙兘鍗￠】 | 闄愬埗鏈€澶?5 鏉℃寚鏍?+ 3 鏉℃瘮杈冿紝浣跨敤 `series.priceScale().applyOptions` 璋冧紭 |

---

## 7. 缁撹

- 浠?lightweight-charts + CTP tick 鏋勫缓鍏ㄦ柊 K 绾跨郴缁熸槸鍙鐨勶紝浣嗛渶瑕?**鍚庣鏁版嵁绱Н** 涓?**鍓嶇缁勪欢閲嶆瀯** 鍚屾鎺ㄨ繘銆? 
- 鐭湡鍙厛钀藉湴 TradingView + 瀹炴椂 tick 闈㈡澘锛屼腑鏈熼€愭鎺ュ叆鑷缓 bar & 鎸囨爣锛屾渶缁堝畬鍏ㄦ浛鎹?AlphaVantage 渚濊禆銆? 
- 鏈枃鎵€鍒楃殑鍒嗛樁娈佃鍒掍笌缁勪欢璁捐锛屽彲鐩存帴浣滀负瀹炴柦钃濆浘銆備笅涓€姝ュ嵆寮€濮?Phase A锛屽苟涓?Phase B/C 鍑嗗 mock 鏁版嵁涓?UI 鍘熷瀷銆? 
