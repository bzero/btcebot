import btceapi

pair = "btc_usd"
    
def main_loop(cnn):
    mins = 0
    while mins != 20:
        ## todo

        time.sleep(10)
        mins += 1
    
def main():
    cnn = btceapi.BTCEConnection()
    trade_fee = btceapi.get_fee(cnn, pair)
    print trade_fee
    history = btceapi.get_history(cnn, pair)
    print history
    ticker = btceapi.get_ticker(cnn, pair)
    print ticker
    book = btceapi.get_book(cnn, pair)
    print book
    
    #main_loop(cnn)
        
    
if __name__ == "__main__":
    main()
    