import datetime 
from subprocess import call
import os
from random import randint
#ledger={}
block_chain={}
accepted_block_reward=50
no_of_users=0
unconfirmed_transactions={}
total_blocks=0
last_block_hash=""

class block:
    def __init__(self,miner,prev_hash,transactions,nonce):
        global total_blocks
        self.block_no=total_blocks
        total_blocks+=1
        self.no_of_transactions=len(transactions)+1
        self.timestamp=datetime.datetime.now()
        self.miner=miner.decode()
        self.hash_string=str(self.no_of_transactions)+self.miner+str(self.timestamp)+str(nonce)
        with open("block_hash_string.txt","wb") as f:
            f.write(bytes(self.hash_string,encoding='utf-8'))
        cmd = "openssl dgst -sha256 -out temp_block_hash.bin block_hash_string.txt"
        call(cmd,shell=True)
        with open("temp_block_hash.bin","rb") as f:
            self.block_hash = f.read().decode().split("=")[1]
        self.prev_hash=prev_hash
        self.next_hash=-1
        self.nonce=nonce
        self.block_reward=accepted_block_reward
        self.transactions=[transaction(coinbase_flag=1,sender_pbk="",reciever_pbk=self.miner,amount=accepted_block_reward,signed_amt="",time_stamp=self.timestamp)]
        self.transactions+=transactions



class transaction:
    def __init__(self,sender_pbk,reciever_pbk,amount,time_stamp,signed_amt,coinbase_flag=0):
        self.time_stamp=time_stamp
        if(coinbase_flag==0):
            self.sender_pbk=sender_pbk.decode()
            self.reciever_pbk=reciever_pbk.decode()
            self.confirm_status="unconfirmed"
        else:
            self.sender_pbk="Coinbase(Newly Generated Coins)"
            self.reciever_pbk=reciever_pbk
            self.confirm_status="confirmed"
        self.signed_amt=signed_amt
        self.amount=amount
        self.block_hash=""
        self.input_utxos=""
        self.change=0
        self.hash_string=str(amount)+self.sender_pbk+self.reciever_pbk+str(time_stamp)
        with open("hash_string.txt","wb") as f:
            f.write(bytes(self.hash_string,encoding='utf-8'))
        cmd = "openssl dgst -sha256 -out temp_hash.bin hash_string.txt"
        call(cmd,shell=True)
        with open("temp_hash.bin","rb") as f:
            self.transaction_hash = f.read().decode().split("= ")[1][:-1]
        self.output_utxos=""
        
        

class user:
    def __init__(self):
        global no_of_users
        no_of_users+=1
        self.username="unknown"
        self.private_key="private-key"+str(no_of_users)+".pem"
        self.public_key="public-key"+str(no_of_users)+".pem"
        cmd="openssl ecparam -name secp256k1 -genkey -noout -out "+self.private_key #ECDSA or ECDSA (Elliptic Curve Digital Signature Algorithm)
        call(cmd,shell=True)
        cmd="openssl ec -in "+self.private_key+" -pubout -out "+self.public_key
        call(cmd,shell=True)
        with open(self.private_key,"rb") as f:
            self.prk = f.read()
        with open(self.public_key,"rb") as f:
            self.pbk = f.read()
        

def create_transaction(spbk,rpbk,amount,signed_amt):
    print("\n--Creating Transaction")
    with open(spbk,"rb") as f:
            sender_pbk=f.read()
    with open(rpbk,"rb") as f:
            reciever_pbk=f.read()
    new_transaction=transaction(sender_pbk=sender_pbk,reciever_pbk=reciever_pbk,amount=amount,time_stamp=datetime.datetime.now(),signed_amt=signed_amt)
    unconfirmed_transactions[new_transaction.transaction_hash]=new_transaction
    print("--Transaction added to Unconfirmed Transactions")

def sign_amount(amount,prk):
    #verification_message="This message is used to verify user"
    with open("amount.txt","wb") as f:
            f.write(bytes(str(amount),encoding='utf8'))
    """
    with open("verify_prk.pem","wb") as f:
            f.write(prk)
    
    with open("verify_pbk.pem","wb") as f:
            f.write(pbk)
    """
    cmd="openssl sha256 -sign "+prk+" -out signed_message.txt amount.txt"
    #print(cmd)
    call(cmd)
    with open("signed_message.txt","rb") as f:
            signed_message=f.read()
    #cmd="openssl dgst -sha256 -verify "+pbk+" -signature signed_message.txt verify_user.txt"
    #result=call(cmd)
    return signed_message

def verify_transaction(tr):
    global last_block_hash
    sender=tr.sender_pbk
    block_pointer=last_block_hash
    #print(block_pointer)
    signed_amount=tr.signed_amt
    #print(sender)
    with open("sender_pbk.pem","wb") as f:
            f.write(bytes(sender,encoding='utf8'))
    with open("signed_amt.txt","wb") as f:
        f.write(signed_amount)
    with open("verify_amount.txt","wb") as f:
            f.write(bytes(str(tr.amount),encoding='utf8'))
    print("--Verifying Sender")
    cmd="openssl dgst -sha256 -verify sender_pbk.pem -signature signed_amt.txt verify_amount.txt"
    result=call(cmd)
    if(result==0):
        stop_flag=0
        sender_wallet=0
        while(block_pointer!="" and stop_flag!=1):
            bl=block_chain[block_pointer]
            for i in range(bl.no_of_transactions):
                if(bl.transactions[i].reciever_pbk==tr.sender_pbk):
                    sender_wallet+=bl.transactions[i].amount
                if(bl.transactions[i].sender_pbk==tr.sender_pbk):
                    stop_flag=1
                    #sender_wallet-=bl.transactions[i].amount
                    sender_wallet+=bl.transactions[i].change
            block_pointer=bl.prev_hash
                    
        if(sender_wallet<tr.amount):
            print("[INVALID TRANSACTION] Insufficient Balence of Sender")
            return 0
        else:
            tr.change=sender_wallet-tr.amount
            print("[VALID TRANSACTION]")
            return 1
    else:
        return 0




def create_genesis_block():
    global last_block_hash
    with open('public-key1.pem',"rb") as f:
                pbk=f.read()
    gb=block(miner=pbk,transactions=[],nonce=randint(0,5000000),prev_hash="")
    block_chain[gb.block_hash]=gb
    last_block_hash=gb.block_hash

if __name__=="__main__":
    create_genesis_block()
    print("Welcome\n")
    c=-1
    while(c!=4):
        c=int(input("\n0.New User\n1.Transcat\n2.Mine\n3.View BlockChain\n4.Exit\n"))
        if(c==0):
            nu=user()
            print("Your Private Key is : \n",nu.prk.decode())
            print("\nYour Public Key is : \n",nu.pbk.decode())
            print("")
        elif(c==1):
            prk=input("Enter your private key : \n")
            pbk=input("Enter your public key : \n")
            r_pbk=input("Enter Reciver's public Key : \n")
            amt=float(input("Enter Amount : "))
            #result=verify_user(prk,pbk)
            #if(result==0):
            signed_amt=sign_amount(amount=amt,prk=prk)
            create_transaction(spbk=pbk,rpbk=r_pbk,amount=amt,signed_amt=signed_amt)
        elif(c==2):
            print("\nUnconfirmed Transactions :\n")
            for i in unconfirmed_transactions:
                #print(i)
                print("\n-----------------------------------------------------\n")
                print("Transaction Hash : \n",unconfirmed_transactions[i].transaction_hash)
                print("\nSender : \n",unconfirmed_transactions[i].sender_pbk)
                print("\nReciever : \n",unconfirmed_transactions[i].reciever_pbk)
                print("\nAmount : ",unconfirmed_transactions[i].amount)
                print("\n-------------------------------------------\n")
            
            miner_key=input("Enter your public key : ")
            with open(miner_key,"rb") as f:
                mk=f.read()
            d=0
            verified_transactions=[]
            while(d==0):
                
                #"""
                try:
                    th=input("Enter Hash of transaction to confirm :\n")
                    tr=unconfirmed_transactions[th] 
                    
                    verified=verify_transaction(tr)
                    if(verified==1):
                        tr.confirm_status="confirmed"
                        verified_transactions.append(tr)
                    unconfirmed_transactions.pop(th)
                except Exception as e:
                    print(e)
                #"""
                d=int(input("\n0.Continue\n1.End\n"))
            #if(len(verified_transactions)>0):
            gb=block(miner=mk,transactions=verified_transactions,nonce=randint(0,5000000),prev_hash=last_block_hash)
            block_chain[gb.block_hash]=gb
            last_block_hash=gb.block_hash
            print("[SUCCESS] Block Placed Successfully")

        elif(c==3):
            for i in block_chain:
                #print(i)
                print("\n-------------------Start of Block----------------------------------\n")
                print("Block Hash : \n",block_chain[i].block_hash)
                print("\nMiner : \n",block_chain[i].miner)
                print("\nDate-Time : ",block_chain[i].timestamp)
                print("\nNo of transactions : ",block_chain[i].no_of_transactions)
                print("\nNonce : ",block_chain[i].nonce)
                tvol=0
                for j in range(block_chain[i].no_of_transactions):
                    if(j!=0):
                        tvol+=block_chain[i].transactions[j].amount
                print("\nTransaction Volume : ",tvol)
                print("\nBlock Reward : ",block_chain[i].block_reward)
                print("\nTransactions : \n")
                for j in range(block_chain[i].no_of_transactions):
                    print("\n     --------------Transaction Start-----------------------------\n")
                    print("     Index : ",j)
                    print("Transaction Hash : ",block_chain[i].transactions[j].transaction_hash)
                    print("\nSender : \n",block_chain[i].transactions[j].sender_pbk)
                    print("\nReciever : \n",block_chain[i].transactions[j].reciever_pbk)
                    print("\nAmount : ",block_chain[i].transactions[j].amount)
                    print("\n     ---------------Transaction End----------------------------\n")
                print("\n-------------------End of Block------------------------\n")






        


