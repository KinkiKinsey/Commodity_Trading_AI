#include "ThostFtdcMdApi.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <atomic>
#include <thread>
#include <chrono>

static std::atomic<bool> gotTick{false};

class OneShotMdSpi : public CThostFtdcMdSpi {
public:
    OneShotMdSpi(CThostFtdcMdApi* api,
                 const char* broker,
                 const char* user,
                 const char* password,
                 const char* instrument)
    : api_(api) {
        strncpy(brokerId_, broker, sizeof(brokerId_) - 1);
        strncpy(userId_, user, sizeof(userId_) - 1);
        strncpy(password_, password, sizeof(password_) - 1);
        strncpy(instrumentId_, instrument, sizeof(instrumentId_) - 1);
    }

    virtual void OnFrontConnected() override {
        CThostFtdcReqUserLoginField req{};
        strncpy(req.BrokerID, brokerId_, sizeof(req.BrokerID) - 1);
        strncpy(req.UserID, userId_, sizeof(req.UserID) - 1);
        strncpy(req.Password, password_, sizeof(req.Password) - 1);
        api_->ReqUserLogin(&req, 1);
    }

    virtual void OnRspUserLogin(CThostFtdcRspUserLoginField* login,
                                CThostFtdcRspInfoField* info,
                                int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            fprintf(stderr, "{\"error\":%d,\"message\":\"%s\"}\n", info->ErrorID, info->ErrorMsg);
            std::fflush(stderr);
            std::exit(2);
        }
        char* ids[1];
        ids[0] = instrumentId_;
        api_->SubscribeMarketData(ids, 1);
    }

    virtual void OnRspSubMarketData(CThostFtdcSpecificInstrumentField* inst,
                                    CThostFtdcRspInfoField* info,
                                    int reqId, bool isLast) override {
        if (info && info->ErrorID != 0) {
            fprintf(stderr, "{\"error\":%d,\"message\":\"%s\"}\n", info->ErrorID, info->ErrorMsg);
            std::fflush(stderr);
            std::exit(3);
        }
    }

    virtual void OnRtnDepthMarketData(CThostFtdcDepthMarketDataField* d) override {
        if (gotTick.exchange(true)) return;
        // Compose epoch-ish string using TradingDay + UpdateTime + UpdateMillisec left to client; we print core fields
        printf("{\"instrument_id\":\"%s\",\"last_price\":%.8f,\"volume\":%d,\"trading_day\":\"%s\",\"update_time\":\"%s\",\"update_millisec\":%d}\n",
               d->InstrumentID, d->LastPrice, d->Volume, d->TradingDay, d->UpdateTime, d->UpdateMillisec);
        std::fflush(stdout);
        std::exit(0);
    }

private:
    CThostFtdcMdApi* api_;
    char brokerId_[32]{};
    char userId_[32]{};
    char password_[41]{};
    char instrumentId_[81]{};
};

int main(int argc, char** argv) {
    if (argc < 6) {
        fprintf(stderr, "Usage: %s tcp://ip:port brokerId userId password instrumentId\n", argv[0]);
        return 1;
    }
    const char* front = argv[1];
    const char* broker = argv[2];
    const char* user = argv[3];
    const char* password = argv[4];
    const char* instrument = argv[5];

    CThostFtdcMdApi* api = CThostFtdcMdApi::CreateFtdcMdApi();
    OneShotMdSpi* spi = new OneShotMdSpi(api, broker, user, password, instrument);
    api->RegisterSpi(spi);
    api->RegisterFront(const_cast<char*>(front));
    api->Init();

    // Block until exit() from callbacks
    while (true) { std::this_thread::sleep_for(std::chrono::seconds(1)); }
    return 0;
}


