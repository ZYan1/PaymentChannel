import pandas as pd
#import matplotlib.pyplot as plt

file_path = "C:/Users/zflip/Zhangyan/1_PaymentChannel/Ethereum_program/noDispute_data/high_gas_noDispute_data.xlsx"
#file_path = "C:/Users/zflip/Zhangyan/1_PaymentChannel/Ethereum_program/Dispute_data/low_Dispute_data.xlsx"

def save_fundingFee_to_excel(data):
    
    data = {" Funding Fee(RbV) ": [data] }
    df = pd.DataFrame(data)

    
    try:
        
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        
        pass

    
    df.to_excel(file_path, index=False)
    print("Funding fee saved to Excel.")

def save_Fee_to_excel(data):
    
    data = {" Fee(RbV) ": [data] }
    df = pd.DataFrame(data)

    
  
    try:
        
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        
        pass

    
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")


def save_Latency_to_excel(data):
    
    data = {" Latency(RbV) ": [data] }
    df = pd.DataFrame(data)

   
    try:
        
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        
        pass

   
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")

def save_Throughput_to_excel(data):
    
    data = {" Throughput(/s)(RbV) ": [data] }
    df = pd.DataFrame(data)

    
    try:
        
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        
        pass

    
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")

