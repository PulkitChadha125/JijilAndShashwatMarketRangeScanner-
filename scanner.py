from kite_trade import *
import pyotp
import time as sleep_time
import pandas as pd
from datetime import datetime
import Zerodha_Integration
import threading
lock = threading.Lock()

def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')

def calculate_percentage_values(value, percentage):
    final = (float(percentage) / 100) * float(value)
    return final


def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_zerodha_credentials():
    delete_file_contents("OrderLog.txt")
    credentials = {}
    try:
        df = pd.read_csv('ZerodhaCredentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials


credentials_dict = get_zerodha_credentials()
user_id = credentials_dict.get('ZerodhaUserId')  # Login Id
password = credentials_dict.get('ZerodhaPassword')  # Login password
fakey = credentials_dict.get('Zerodha2fa')
BuyBufferPercentage = float(credentials_dict.get('BuyBufferPercentage'))
SellBufferPercentage = float(credentials_dict.get('SellBufferPercentage'))
StoplossPercentage = float(credentials_dict.get('StoplossPercentage'))
Target1Percentage =float( credentials_dict.get('Target1Percentage'))
Target2Percentage =float( credentials_dict.get('Target2Percentage'))
Target3Percentage =float( credentials_dict.get('Target3Percentage'))
TSLPercentage =float( credentials_dict.get('TSLPercentage'))
TotalAmountQty=float( credentials_dict.get('TotalAmountQty'))
Lot1_percentage=float( credentials_dict.get('Lot1_percentage'))
Lot2_percentage=float( credentials_dict.get('Lot2_percentage'))
Lot3_percentage=float( credentials_dict.get('Lot3_percentage'))
Leverage_multiplier=float( credentials_dict.get('Leverage_multiplier'))

twofa = pyotp.TOTP(fakey)
twofa = twofa.now()
kite = Zerodha_Integration.login(user_id, password, twofa)
symbol_dict={}
priority_dict={}
formatted_symbols=None
def my_trade_universe():
    global BuyBufferPercentage ,SellBufferPercentage , Leverage_multiplier, Lot3_percentage,Lot2_percentage, Lot1_percentage,TotalAmountQty, symbol_dict, formatted_symbols,StoplossPercentage,Target1Percentage,Target2Percentage,Target3Percentage,TSLPercentage
    try:
        df = pd.read_csv('MYINSTRUMENTS.csv')
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("start time:", current_time)
        for symbol in df['Symbol']:
            try:
                previousclose= Zerodha_Integration.get_prevous_close(symbol)

                buyval=calculate_percentage_values(previousclose,BuyBufferPercentage)
                buyval=previousclose+buyval

                sellval=calculate_percentage_values(previousclose,SellBufferPercentage)
                sellval=previousclose-sellval

                symbol_dict[symbol] = {
                    "previousclose": previousclose,
                    "buyval": buyval,
                    "sellval": sellval,
                    "stoplossval": 0,
                    "tp1": 0,
                    "tp2": 0,
                    "tp3": 0,
                    "tp1qty": 0,
                    "tp2qty": 0,
                    "tp3qty": 0,
                    "slqty": 0,
                    "totalqty":0,
                    "stoplos_bool": False,
                    "tp1_bool": False,
                    "tp2_bool": False,
                    "tp3_bool": False,
                    "tradetype": None,
                    "tslstep":0,
                    "tslmove":0,
                    "tslval":0,
                }
                formatted_symbols = [f'NSE: {symbol}' for symbol in symbol_dict.keys()]
            except Exception as e:
                print(f"An error occurred for symbol {symbol}: {str(e)}")

        # print(symbol_dict)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("stop time:", current_time)
        print(symbol_dict)
    except Exception as e:
        print("An error occurred while reading the MYINSTRUMENTS.CSV file:", str(e))


def check_orders(symbol_dict):
    global Leverage_multiplier, Lot3_percentage,Lot2_percentage, Lot1_percentage,TotalAmountQty,formatted_symbols, TradeBufferPercentage, StoplossPercentage, Target1Percentage, Target2Percentage, Target3Percentage, TSLPercentage

    for symbol, data in symbol_dict.items():
        try:
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            ltp = float(Zerodha_Integration.get_ltp(symbol))

            if data['tradetype'] is None and float(data['buyval'] ) > 0 and float(ltp) > float(data['buyval']):
                ltp = float(Zerodha_Integration.get_ltp(symbol))
                data['tradetype']="BUY"
                data["stoplos_bool"]=True
                data["tp1_bool"]=True
                data["tp2_bool"]=True
                data["tp3_bool"]=True
                brokermargin = Zerodha_Integration.get_margin()
                print("present broker margin : ",brokermargin)


                amounttotrade= calculate_percentage_values(brokermargin,TotalAmountQty)
                print("amounttotrade: ",amounttotrade)
                print("ltp", ltp)
                totalqty= int(amounttotrade/ltp)


                print("totalqty1: ",totalqty)

                totalqty= totalqty * Leverage_multiplier
                print("totalqty2: ", totalqty)



                data["slqty"]=totalqty
                data["totalqty"]= totalqty
                tp1qty=calculate_percentage_values(totalqty,Lot1_percentage)
                tp1qty=int(tp1qty)
                data["tp1qty"] = tp1qty

                tp2qty = calculate_percentage_values(totalqty, Lot2_percentage)
                tp2qty = int(tp2qty)
                data["tp2qty"] = tp2qty

                tp3qty= totalqty-tp1qty
                tp3qty=tp3qty-tp2qty
                tp3qty=int(tp2qty)
                data["tp3qty"] = tp3qty

                tp1 =calculate_percentage_values(data["buyval"],Target1Percentage)
                tp1 = data["buyval"] + tp1
                data['tp1']= tp1

                tp2 =calculate_percentage_values(data["buyval"],Target2Percentage)
                tp2 = data["buyval"] + tp2
                data['tp2']= tp2

                tp3 = calculate_percentage_values(data["buyval"], Target3Percentage)
                tp3 = data["buyval"] + tp3
                data['tp3'] = tp3

                stoplossval=calculate_percentage_values(data["buyval"], StoplossPercentage)
                stoplossval = data["buyval"] - stoplossval
                data['stoplossval'] = stoplossval

                data["tslval"] = calculate_percentage_values(ltp, TSLPercentage)

                data["tslstep"] = ltp + data["tslval"]

                orderlog = f"{timestamp} Buy order executed for {symbol} for lotsize= {totalqty}  @ {ltp} ,Target1 ={tp1},Target2 ={tp2},Target3 ={tp3}, TslStep= {data['tslstep']}  And Stoploss ={stoplossval}"
                print(orderlog)
                write_to_order_logs(orderlog)
                Zerodha_Integration.buy(symbol,int(totalqty))


            if data['tradetype'] is None and float(data['sellval']) > 0 and float(ltp) < float(data['sellval']):
                data['tradetype'] = "SHORT"
                data["stoplos_bool"] = True
                data["tp1_bool"] = True
                data["tp2_bool"] = True
                data["tp3_bool"] = True
                brokermargin = Zerodha_Integration.get_margin()
                print("present broker margin : ", brokermargin)
                amounttotrade = calculate_percentage_values(brokermargin, TotalAmountQty)
                totalqty = int(amounttotrade / ltp)
                totalqty = totalqty * Leverage_multiplier
                data["slqty"] = totalqty
                data["totalqty"] = totalqty

                tp1qty = calculate_percentage_values(totalqty, Lot1_percentage)
                tp1qty = int(tp1qty)
                data["tp1qty"] = tp1qty

                tp2qty = calculate_percentage_values(totalqty, Lot2_percentage)
                tp2qty = int(tp2qty)
                data["tp2qty"] = tp2qty

                tp3qty = totalqty - tp1qty
                tp3qty = tp3qty - tp2qty
                tp3qty = int(tp2qty)
                data["tp3qty"] = tp3qty


                tp1 = calculate_percentage_values(data["sellval"], Target1Percentage)
                tp1 = data["sellval"] - tp1
                data['tp1'] = tp1

                tp2 = calculate_percentage_values(data["sellval"], Target2Percentage)
                tp2 = data["buyval"] - tp2
                data['tp2'] = tp2

                tp3 = calculate_percentage_values(data["sellval"], Target3Percentage)
                tp3 = data["sellval"] - tp3
                data['tp3'] = tp3

                stoplossval = calculate_percentage_values(data["sellval"], StoplossPercentage)
                stoplossval = data["sellval"] + stoplossval
                data['stoplossval'] = stoplossval

                data["tslval"] = calculate_percentage_values(ltp, TSLPercentage)
                data["tslstep"] = ltp - data["tslval"]


                Zerodha_Integration.short(symbol,int( totalqty))
                orderlog = f"{timestamp} sell order executed for {symbol} for lotsize= {totalqty} @ {ltp} ,Target1 ={tp1},Target2 ={tp2},Target3 ={tp3}, TslStep= {data['tslstep']} And Stoploss ={stoplossval} "
                print(orderlog)
                write_to_order_logs(orderlog)

            net_positions=Zerodha_Integration.get_position()
            if any(pos['tradingsymbol'] == symbol for pos in net_positions.get('net', [])):
                # Find the position for the symbol
                position = next((pos for pos in net_positions['net'] if pos['tradingsymbol'] == symbol), None)
                if position and 'quantity' in position:
                    quantity = position['quantity']
                    print(f"Quantity for {symbol}: {quantity}")

                    # Now you can use 'quantity' as needed in your logic


                if quantity>0 and data['tradetype']== "BUY" and float(ltp) >= float(data["tslstep"]):

                    data["tslstep"]= data["tslstep"]+data["tslval"]
                    data['stoplossval']=data['stoplossval']+data["tslval"]


                    orderlog = f"{timestamp} Tsl executed {symbol} for lotsize=  @ {ltp} new  Stoploss ={data['stoplossval']}"
                    print(orderlog)
                    write_to_order_logs(orderlog)

                if quantity>0 and data['tradetype']== "SHORT" and float(ltp) <= float(data["tslstep"]):
                    data["tslstep"]= ltp-data["tslval"]
                    data['stoplossval']=data['stoplossval']-data["tslval"]
                    orderlog = f"{timestamp} Tsl executed {symbol} for lotsize=  @ {ltp} new  Stoploss ={data['stoplossval']}"
                    print(orderlog)
                    write_to_order_logs(orderlog)




                if quantity > 0 and data['tradetype']== "BUY" and float(ltp) >= float(data['tp1']) and float(data['tp1']) > 0 and data["tp1_bool"] == True:
                    data["tp1_bool"]=False
                    data["slqty"] = int(data["slqty"])-int(data["tp1qty"])

                    Zerodha_Integration.sell(symbol, int(data["tp1qty"]))
                    orderlog = f"{timestamp} Buy Target 1 executed {symbol} @ {data['tp1']}"
                    data['tp1']=0
                    write_to_order_logs(orderlog)

                if  quantity < 0 and data['tradetype']== "SHORT" and float(ltp) <= float(data['tp1']) and float(data['tp1']) > 0 and data["tp1_bool"] == True:
                    data["tp1_bool"]=False
                    data["slqty"] = int(data["slqty"]) - int(data["tp1qty"])
                    Zerodha_Integration.cover(symbol, int(data["tp1qty"]))
                    orderlog = f"{timestamp} Sell Target 1 executed {symbol} @ {data['tp1']}"
                    data['tp1']=0
                    write_to_order_logs(orderlog)

                if quantity > 0 and data['tradetype']== "BUY" and float(ltp) >= float(data['tp2']) and float(data['tp2']) > 0 and data["tp2_bool"] == True:
                    data["tp2_bool"]=False
                    data["slqty"] = int(data["slqty"]) - int(data["tp2qty"])
                    Zerodha_Integration.sell(symbol, int(data["tp2qty"]))
                    orderlog = f"{timestamp} Buy Target 2 executed {symbol} @ {data['tp2']}"
                    data['tp2']=0
                    write_to_order_logs(orderlog)

                if quantity < 0 and data['tradetype']== "SHORT" and float(ltp) <= float(data['tp2']) and float(data['tp2']) > 0 and data["tp2_bool"] == True:
                    data["tp2_bool"]=False
                    data["slqty"] = int(data["slqty"]) - int(data["tp2qty"])
                    Zerodha_Integration.cover(symbol, int(data["tp2qty"]))
                    orderlog = f"{timestamp} Sell Target 2 executed {symbol} @ {data['tp2']}"
                    data['tp2']=0
                    write_to_order_logs(orderlog)

                if quantity > 0 and data['tradetype']== "BUY" and float(ltp) >= float(data['tp3']) and float(data['tp3']) > 0 and data["tp3_bool"] == True:
                    data["tp3_bool"]=False
                    data["slqty"] = 0
                    Zerodha_Integration.sell(symbol, int(data["tp3qty"]))
                    orderlog = f"{timestamp} Buy Target 3 executed {symbol} @ {data['tp3']}"
                    data['tp3']=0
                    write_to_order_logs(orderlog)
                    data['tradetype'] = "TradeDone"

                if quantity < 0 and data['tradetype']== "SHORT" and float(ltp) <= float(data['tp3'] )and float(data['tp3']) > 0 and data["tp3_bool"] == True:
                    data["tp3_bool"]=False
                    data["slqty"] = 0
                    Zerodha_Integration.cover(symbol, int(data["tp3qty"]))
                    orderlog = f"{timestamp} Short Target 3 executed {symbol} @ {data['tp3']}"
                    data['tp3']=0
                    write_to_order_logs(orderlog)
                    data['tradetype'] = "TradeDone"

                if quantity > 0 and data['tradetype']== "BUY" and float(ltp) <= float(data['stoplossval']) and float( data['stoplossval'] ) > 0 and data["stoplos_bool"] == True:
                    data["stoplos_bool"]=False
                    Zerodha_Integration.sell(symbol, 1)
                    orderlog = f"{timestamp} Buy Stoploss executed {symbol} @ {data['tp3']}"
                    data['tp3']=0
                    write_to_order_logs(orderlog)
                    data['tradetype'] = "TradeDone"

                if quantity < 0 and data['tradetype']== "SHORT" and float(ltp) >= float(data['stoplossval']) and float(data['stoplossval']) > 0 and data["stoplos_bool"] == True:
                    data["stoplos_bool"]=False
                    Zerodha_Integration.cover(symbol, int(data["slqty"]))
                    orderlog = f"{timestamp} Short Stoploss executed {symbol} @ {data['tp3']}"
                    data['tp3']=0
                    write_to_order_logs(orderlog)
                    data['tradetype'] = "TradeDone"






        except Exception as e:
            print(f"error happened in order placement  {symbol}: {str(e)}")













def mainstrategy():
    global Leverage_multiplier
    strattime = credentials_dict.get('StartTime')
    stoptime = credentials_dict.get('Stoptime')
    start_time = datetime.strptime(strattime, '%H:%M').time()
    stop_time = datetime.strptime(stoptime, '%H:%M').time()
    while True:
        now = datetime.now().time()
        if now >= start_time and now < stop_time:
            check_orders(symbol_dict)
            sleep_time.sleep(1)


my_trade_universe()
mainstrategy()