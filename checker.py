import requests
import json
import sys
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# =====================================================================
# ⚙️ БЛОК КОНФИГУРАЦИИ СИСТЕМЫ (ВЫНЕСЕН НА САМЫЙ ВЕРХ ФАЙЛА)
# =====================================================================
API_KEY = "YOUR_ETHERSCAN_API_KEY_HERE"
URL_GATEWAY = "https://api.etherscan.io/v2/api"
# =====================================================================

LISTEN_PORT = 5005  # Чекер будет слушать этот свободный порт!


def analyze_smart_contract_security(contract_name, source_code):
    report = {
        "contract_name": contract_name,
        "block_time_risk": "SAFE",
        "drift_factor": 1.0,
        "vulnerabilities": [ ]
    }

    has_block_number = "block.number" in source_code or "blockNumber" in source_code
    has_assembly_number = "number()" in source_code or ("assembly" in source_code and "number" in source_code)
    has_blockhash_drift = "blockhash(" in source_code

    if has_block_number or has_assembly_number or has_blockhash_drift:
        report["block_time_risk"] = "HIGH RISK 🚨"
        intended_block_time = 3.0
        current_block_time = 0.45
        report["drift_factor"] = round(intended_block_time / current_block_time, 2)

    if "selfdestruct" in source_code or "suicide(" in source_code:
        report["vulnerabilities"].append("CRITICAL: selfdestruct Backdoor Found ⚠️")

 #   if "nonreentrant" not in source_code.lower() and ("withdraw" in source_code.lower() or "transfer" in source_code.lower()):
 #       report["vulnerabilities"].append("WARNING: Missing Reentrancy Protection ⚠️")

    if "nonreentrant" not in source_code.lower() and ("withdraw" in source_code.lower() or "transfer" in source_code.lower()):
        report["vulnerabilities"].append(
            "WARNING: Missing Reentrancy Protection ⚠️<br>"
            "↳ Note: This is a warning, not a definitive exploit. If the contract securely implements "
            "the 'Checks-Effects-Interactions' pattern (modifying state/balances BEFORE executing external transfers), "
            "it is safe from reentrancy attacks. However, adding OpenZeppelin's nonReentrant modifier is recommended "
            "for absolute contract infrastructure depth."
        )

    if "tx.origin" in source_code:
        report["vulnerabilities"].append("WARNING: Phishing Risk via tx.origin ⚠️")

    return report

def get_bsc_contract_code(contract_address, api_key, url):
    params = {
        "chainid": "56",
        "module": "contract",
        "action": "getsourcecode",
        "address": contract_address,
        "apikey": api_key
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if not response.text: return None, "Empty API Response"
        data_json = response.json()
    except Exception as e:
        return None, f"Network Error: {str(e)}"

    if data_json.get("status") == "1" and data_json.get("result"):
        result_list = data_json["result"]

        # 🛡️ ТОТАЛЬНЫЙ МНОГОУРОВНЕВЫЙ ФИКС РАСПАКОВКИ СПИСКОВ API V2
        if isinstance(result_list, list) and len(result_list) > 0:
            first_level = result_list[ 0 ]
            if isinstance(first_level, list) and len(first_level) > 0:
                contract_data = first_level[ 0 ]
            else:
                contract_data = first_level

            return contract_data.get("ContractName"), contract_data.get("SourceCode")

    return None, f"Blockchain API Error: {data_json.get('result', 'Unknown')}"

class CheckerAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

        address_list = query_params.get("address")
        if not address_list:
            error_response = {"status": "error", "message": "🚨 Missing ?address= parameter"}
            self.wfile.write(json.dumps(error_response).encode("utf-8"))
            return

        target_address = address_list[ 0 ].strip()
        name, code = get_bsc_contract_code(target_address, API_KEY, URL_GATEWAY)

        if name and code:
            final_report = analyze_smart_contract_security(name, code)
            final_report["status"] = "success"
            self.wfile.write(json.dumps(final_report, ensure_ascii=False).encode("utf-8"))
        else:
            error_msg = name if name else code
            error_response = {"status": "error", "message": f"❌ {error_msg}"}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8"))

def run_server():
    if API_KEY == "ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ_ОТ_ETHERSCAN":
        print("🚨 ERROR: Forgot to set API Key on line 9!")
        sys.exit(1)

    server_address = ("", LISTEN_PORT)
    httpd = HTTPServer(server_address, CheckerAPIHandler)
    print(f"🚀 Checker Server is live on port {LISTEN_PORT}...")
    try: httpd.serve_forever()
    except KeyboardInterrupt: print("\n🛑 Server stopped.")

if __name__ == "__main__":
    run_server()
