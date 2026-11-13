import asyncio
from web3 import AsyncWeb3 as asweb3
from pathlib import Path
import time, json
VALID_RPC = []
battle_rpc = []
NODES_PATH = Path(__file__).resolve().parent / "config/nodes.json"
with open(NODES_PATH, "r", encoding="utf-8") as node:
     RPC_URL_ALL = json.load(node)
    

CONFIG_PATH = Path(__file__).resolve().parent / "config/config.json"
async def fight(Arpc, Brpc):
    w3 = asweb3(asweb3.AsyncHTTPProvider(Arpc))
    w2 = asweb3(asweb3.AsyncHTTPProvider(Brpc))
    try:
        await asyncio.sleep(2)
        print("GO " + str(len(battle_rpc)) + " participant")
        start = time.perf_counter()
        #FIGHT
        async def measure_ping(w, name):
            start = time.perf_counter()
            try:
                await w.eth.block_number
                return name, (time.perf_counter() - start) * 1000
            except Exception:
                return name, 9999999.0

        results = await asyncio.gather(
            measure_ping(w3, Arpc),
            measure_ping(w2, Brpc)
        )
        if results[0][0] == Arpc:
            lat_ms_a = results[0][1]
            lat_ms_b = results[1][1]
        else:
            lat_ms_a = results[1][1]
            lat_ms_b = results[0][1]

        if lat_ms_a < lat_ms_b:
            winner = lat_ms_a
            print(f"[WINNER] NODE {winner} | lat: {lat_ms_a:.2f} ms")
            battle_rpc.remove(Brpc)
            return [Arpc, lat_ms_a]
        else:
            winner = lat_ms_b
            print(f"[WINNER] NODE {winner} | lat: {lat_ms_b:.2f} ms")
            battle_rpc.remove(Arpc)

            return [Brpc, lat_ms_b]
    except Exception as e:
            print(e)
    finally:
            await w3.provider.disconnect()
            await w2.provider.disconnect()

async def algo_validate_node():
    global RPC_URL
    for rpc in RPC_URL_ALL:
        check = asweb3(asweb3.AsyncHTTPProvider(rpc))
        try:
            is_conn = await asyncio.wait_for(check.is_connected(), timeout=4.0)
            if is_conn:
                VALID_RPC.append(rpc)
                print("[NODE] valid rpc node spotted")
            else:
                print(f"[SHIT] RPC NODE {rpc} was skipped")
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] RPC NODE {rpc} is too slow > 4 sec")
        except Exception as e:
             print(f"[DEAD] RPC NODE {rpc} is dead Reason: {type(e).__name__}: {e}]")
        finally:
            await check.provider.disconnect()

    val_rpc = VALID_RPC
    print(f"VALID RPC COUNT: {len(val_rpc)}")

    #only 1 rpc. sync and time 
    for vrpc in val_rpc:
        pretend = asweb3(asweb3.AsyncHTTPProvider(vrpc))
        try:
            sync = await asyncio.wait_for(pretend.eth.syncing, timeout=3.0)
            if sync != False:
                print(f"[NOT SYNCHED] node {vrpc} is old. test other")
            else:
                battle_rpc.append(vrpc)
        except:
            print(f"node {vrpc} is dead.")
        finally:
                    await pretend.provider.disconnect()
                
    # latency battle
    brpc = battle_rpc
    print(f"[START FIGHT] COUNT RPC IN FIGHT: {len(brpc)}")
    print("starting fight")
    while len(battle_rpc) > 1:
        res = await fight(battle_rpc[-1], battle_rpc[-2])
        print(f"[ROUND] winner {res[0]} | lat: {res[1]:.2f} ms\n")

    if len(battle_rpc) == 1:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)   
        except (FileExistsError, json.JSONDecodeError) as e:
             data = {}
        data["rpc_url"] = battle_rpc[0]

        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
             json.dump(data, file, indent=4, ensure_ascii=False)
        
        print(f"[RESULT] CHAMPION IS {battle_rpc[0]}")
    else:
        raise RuntimeError("No living rpc node")

