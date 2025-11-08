#include "ThostFtdcMdApi.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <atomic>
#include <thread>
#include <chrono>

static std::atomic<bool> finished{false};

class LoginSpi : public CThostFtdcMdSpi {
public:
    LoginSpi(CThostFtdcMdApi* api, const char* broker, const char* user, const char* pwd)
        : api_(api) {
        strncpy(brokerId_, broker, sizeof(brokerId_) - 1);
        strncpy(userId_, user, sizeof(userId_) - 1);
        strncpy(password_, pwd, sizeof(password_) - 1);
    }

    virtual void OnFrontConnected() override {
        CThostFtdcReqUserLoginField req{};
        strncpy(req.BrokerID, brokerId_, sizeof(req.BrokerID) - 1);
        strncpy(req.UserID, userId_, sizeof(req.UserID) - 1);
        strncpy(req.Password, password_, sizeof(req.Password) - 1);
        api_->ReqUserLogin(&req, 1);
    }

    virtual void OnFrontDisconnected(int reason) override {
        if (finished.exchange(true)) return;
        printf("{\"ok\":false,\"disconnected\":%d}\n", reason);
        std::fflush(stdout);
        std::exit(0);
    }

    virtual void OnRspUserLogin(CThostFtdcRspUserLoginField* login,
                                CThostFtdcRspInfoField* info,
                                int reqId, bool isLast) override {
        if (finished.exchange(true)) return;
        if (info && info->ErrorID != 0) {
            printf("{\"ok\":false,\"error_id\":%d,\"error_msg\":\"%s\"}\n", info->ErrorID, info->ErrorMsg);
        } else {
            printf("{\"ok\":true,\"trading_day\":\"%s\"}\n", login ? login->TradingDay : "");
        }
        std::fflush(stdout);
        std::exit(0);
    }

private:
    CThostFtdcMdApi* api_;
    char brokerId_[32]{};
    char userId_[32]{};
    char password_[41]{};
};

int main(int argc, char** argv) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s tcp://ip:port brokerId userId password\n", argv[0]);
        return 1;
    }
    const char* front = argv[1];
    const char* broker = argv[2];
    const char* user = argv[3];
    const char* password = argv[4];

    CThostFtdcMdApi* api = CThostFtdcMdApi::CreateFtdcMdApi();
    LoginSpi* spi = new LoginSpi(api, broker, user, password);
    api->RegisterSpi(spi);
    api->RegisterFront(const_cast<char*>(front));
    api->Init();

    // wait up to 30 seconds
    for (int i = 0; i < 30; ++i) {
        if (finished.load()) break;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    if (!finished.load()) {
        printf("{\"ok\":false,\"timeout\":true}\n");
        std::fflush(stdout);
    }
    return 0;
}


