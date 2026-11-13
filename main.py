import asyncio
import json
from collections import deque
from balancer import algo_validate_node, fight, CONFIG_PATH
from web3 import AsyncWeb3 as asweb3
from pathlib import Path
# init
SCAN_ADDRESS_MAIN = "0xC98b6822cAc177F9bDabF35D566799ab6389B8A5"
start_address = SCAN_ADDRESS_MAIN.lower()
RPC_URL = "eth"
usdt_contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
LOG_PATH = Path(__file__).resolve().parent / "result/logs.txt"
async def connect():
    global RPC_URL
    await algo_validate_node()
        # read
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            RPC_URL = config_data["rpc_url"]
    print(f"\nsucsessfuly set {RPC_URL} rpc_node")


async def main():
      await connect()
      await algosint(start_address)
# {PREPARATION}
receivers = []


async def algosint(adrress):
        # OPTIMIZATION
        queue = deque([adrress])
        visited = set([adrress])
        
        # CONNECT
        w3 = asweb3(asweb3.AsyncHTTPProvider(RPC_URL))
        # OPTIMIZATION #2
        latest = await w3.eth.block_number
        if await w3.is_connected():
              print("connected")
        while queue:
              #
              current_address = queue.popleft()
              padded_target_address = "0x" + ("0" * 24) + current_address[2:]
              TRANSFER_TOPIC = [
                      "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                      padded_target_address
                      ] 
              
              print(f"scanning the node {current_address} ")
              # VARIATION 1 - информационное досье.
              check_sum_adr = asweb3.to_checksum_address(current_address)
              balance = await w3.eth.get_balance(check_sum_adr)
              balance = w3.from_wei(balance, 'ether')
              

              logs = await w3.eth.get_logs({
                    "fromBlock": latest - 1000,
                    "toBlock": "latest",
                    "address": usdt_contract,
                    "topics": TRANSFER_TOPIC
              })
              print("received log's")
              # 1 - sender 2 -  receiver
              for log in logs:
                    sender_addr = "0x" + log["topics"][1].hex()[-40:]
                    receiver_addr = "0x" + log["topics"][2].hex()[-40:]
                    amount_usdt = int(log["data"].hex(), 16) / 1e6
                    tx = log["transactionHash"].hex()

                    # search and analyzing
                    if amount_usdt >= 5000:
                        print(f"  [->] Whale transfer: ${amount_usdt:,.2f} to {receiver_addr}")
                        if receiver_addr not in visited:
                            visited.add(receiver_addr) # бронируем
                            queue.append(receiver_addr) # кидаем на очередь скана
                        print(f"""
                        latest transactions:
                        from {sender_addr} -> to {receiver_addr} | amount {amount_usdt} | tx {tx}
                        Write in logs.

""")
                        with open(LOG_PATH, 'a', encoding='utf-8') as file:
                            file.write(f"from {sender_addr} -> to {receiver_addr} | amount {amount_usdt} USDT | tx {tx} |\n")
        await w3.provider.disconnect()


if __name__ == "__main__":
    asyncio.run(main())