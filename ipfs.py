import requests
import json

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"

    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "pinata_api_key": "5d1b62674a483b38e64d",
        "pinata_secret_api_key": "0388334966e9bcd14111c22a654491d44f753d4272f96b0ab963032bf292c80e"
    }
    payload = {
        "pinataContent": data
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    cid = response.json().get("IpfsHash")
    return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	url = f"https://gateway.pinata.cloud/ipfs/{cid}"

    # Fetch the data
	response = requests.get(url)
	response.raise_for_status()

	if content_type.lower() == "json":
		data = response.json()
	else:
		raise ValueError(f"Unsupported content_type: {content_type}")	

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data

if __name__ == "__main__":
	# test cid
    test_data = {"hello": "world", "number": 123}
    cid = pin_to_ipfs(test_data)
    print("Pinned test JSON to IPFS, CID =", cid)
    # Test pinning
    test_data = {"hello": "world", "number": 123}
    cid = pin_to_ipfs(test_data)
    print("Pinned test JSON to IPFS, CID =", cid)
    # Test retrieval
    fetched = get_from_ipfs(cid)
    print("Fetched back:", fetched)