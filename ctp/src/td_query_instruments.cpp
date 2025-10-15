#include "ThostFtdcTraderApi.h"
#include <iostream>
#include <string>
#include <vector>
#include <atomic>
#include <thread>
#include <chrono>
#include <cstring>

static std::atomic<bool> finished{false};
static std::vector<std::string> instruments;

class QueryInstrumentSpi : public CThostFtdcTraderSpi {
private:
    CThostFtdcTraderApi* api;
    std::string broker_id;
    std::string user_id;
    std::string password;
    bool authenticated = false;

public:
    QueryInstrumentSpi(CThostFtdcTraderApi* pApi, 
                       const std::string& broker,
                       const std::string& user,
                       const std::string& pwd)
        : api(pApi), broker_id(broker), user_id(user), password(pwd) {}

    void OnFrontConnected() override {
        std::cerr << "[INFO] Front connected" << std::endl;
        doAuthenticate();
    }

    void doAuthenticate() {
        CThostFtdcReqAuthenticateField req = {};
        strncpy(req.BrokerID, broker_id.c_str(), sizeof(req.BrokerID) - 1);
        strncpy(req.UserID, user_id.c_str(), sizeof(req.UserID) - 1);
        // AppID and AuthCode are empty (免认证)
        api->ReqAuthenticate(&req, 1);
    }

    void OnRspAuthenticate(CThostFtdcRspAuthenticateField* auth,
                          CThostFtdcRspInfoField* info,
                          int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            std::cerr << "[WARN] Auth failed: " << info->ErrorID << " " 
                      << info->ErrorMsg << ", trying login anyway" << std::endl;
        }
        authenticated = true;
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        doLogin();
    }

    void doLogin() {
        CThostFtdcReqUserLoginField req = {};
        strncpy(req.BrokerID, broker_id.c_str(), sizeof(req.BrokerID) - 1);
        strncpy(req.UserID, user_id.c_str(), sizeof(req.UserID) - 1);
        strncpy(req.Password, password.c_str(), sizeof(req.Password) - 1);
        api->ReqUserLogin(&req, 2);
    }

    void OnRspUserLogin(CThostFtdcRspUserLoginField* login,
                       CThostFtdcRspInfoField* info,
                       int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            if (finished.exchange(true)) return;
            std::cout << "{\"ok\":false,\"error_id\":" << info->ErrorID
                      << ",\"error_msg\":\"" << info->ErrorMsg << "\"}" << std::endl;
            std::exit(1);
        }
        std::cerr << "[INFO] Login successful" << std::endl;
        queryInstruments();
    }

    void queryInstruments() {
        CThostFtdcQryInstrumentField req = {};
        int ret = api->ReqQryInstrument(&req, 3);
        if (ret != 0) {
            std::cerr << "[ERROR] ReqQryInstrument failed: " << ret << std::endl;
        }
    }

    void OnRspQryInstrument(CThostFtdcInstrumentField* inst,
                           CThostFtdcRspInfoField* info,
                           int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            if (finished.exchange(true)) return;
            std::cout << "{\"ok\":false,\"error_id\":" << info->ErrorID
                      << ",\"error_msg\":\"" << info->ErrorMsg << "\"}" << std::endl;
            std::exit(1);
        }

        if (inst) {
            instruments.push_back(inst->InstrumentID);
        }

        if (isLast) {
            if (finished.exchange(true)) return;
            // Output JSON
            std::cout << "{\"ok\":true,\"count\":" << instruments.size()
                      << ",\"instruments\":[";
            for (size_t i = 0; i < instruments.size(); ++i) {
                if (i > 0) std::cout << ",";
                std::cout << "\"" << instruments[i] << "\"";
            }
            std::cout << "]}" << std::endl;
            std::exit(0);
        }
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

    // 创建 flow 文件目录
    system("mkdir -p /tmp/ctp_query_flow");

    CThostFtdcTraderApi* api = CThostFtdcTraderApi::CreateFtdcTraderApi("/tmp/ctp_query_flow/");
    QueryInstrumentSpi* spi = new QueryInstrumentSpi(api, broker, user, password);
    api->RegisterSpi(spi);
    api->RegisterFront(const_cast<char*>(front.c_str()));
    api->SubscribePublicTopic(THOST_TERT_QUICK);
    api->SubscribePrivateTopic(THOST_TERT_QUICK);
    api->Init();

    // Wait up to 120 seconds
    for (int i = 0; i < 120; ++i) {
        if (finished.load()) break;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    if (!finished.load()) {
        std::cout << "{\"ok\":false,\"timeout\":true}" << std::endl;
    }

    return 0;
}


