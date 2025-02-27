import pandas as pd

file_path = "C:/Users/zflip/Zhangyan/1_PaymentChannel/Ethereum_program/noDispute_data/high_gas_noDispute_data.xlsx"
#file_path = "C:/Users/zflip/Zhangyan/1_PaymentChannel/Ethereum_program/Dispute_data/low_Dispute_data.xlsx"

def save_fundingFee_to_excel(data):
    # create a DataFrame
    data = {" Funding Fee(RbR) ": [data] }
    df = pd.DataFrame(data)

    # Check if the file exists, append to it if it does, or create a new file if it does not exist.
    try:
        # Attempt to load an existing file and append data. 
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        # If the file does not exist, directly create a new DataFrame.
        pass

    # Write the DataFrame to an Excel file.
    df.to_excel(file_path, index=False)
    print("Funding fee saved to Excel.")

def save_Fee_to_excel(data):
    # create a DataFrame
    data = {" Fee(RbR) ": [data] }
    df = pd.DataFrame(data)

    # Check if the file exists, append to it if it does, or create a new file if it does not exist.
    
    try:
        # Attempt to load an existing file and append data. 
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        #
        pass

    # Write the DataFrame to an Excel file.
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")

def save_Latency_to_excel(data):
    # create a DataFrame
    data = {" Latency(RbR) ": [data] }
    df = pd.DataFrame(data)

    # Check if the file exists, append to it if it does, or create a new file if it does not exist.
  
    try:
        # Attempt to load an existing file and append data. 
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        # If the file does not exist, directly create a new DataFrame.
        pass

    # Write the DataFrame to an Excel file.
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")

def save_Throughput_to_excel(data):
    # create a DataFrame
    data = {" Throughput(/s)(RbR) ": [data] }
    df = pd.DataFrame(data)

    # Check if the file exists, append to it if it does, or create a new file if it does not exist.
    
    try:
        # Attempt to load an existing file and append data. 
        existing_df = pd.read_excel(file_path, engine="openpyxl")
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        # If the file does not exist, directly create a new DataFrame.
        pass

    #Write the DataFrame to an Excel file.
    df.to_excel(file_path, index=False)
    print("Data saved to Excel.")

