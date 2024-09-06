import requests

def get_wojewodztwa():
    url = "http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/woj.json"
    response = requests.get(url)

    if response.status_code == 200:
        wojewodztwa = response.json()
        devision_dict = {}
        for wojewodztwo in wojewodztwa.get('jednAdms', []):
            wojewodztwo_info = wojewodztwo.get('jednAdm')
            wojewodztwo_id = wojewodztwo_info.get('wojIIPId')
            wojewodztwo_nazwa = wojewodztwo_info.get('wojNazwa')
            devision_dict[wojewodztwo_nazwa] = wojewodztwo_id
        return devision_dict
    else:
        print(f"Błąd: {response.status_code}")
        


def get_powiaty(woj_id):
    url = f"http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/pow/PL.PZGIK.200/{woj_id}/skr.json"
    response = requests.get(url)
 
    if response.status_code == 200:
        powiaty = response.json()
        powiaty_dict = {}
        for powiat in powiaty.get('jednAdms'):
            powiat_info = powiat.get('jednAdm')
            powiat_id = powiat_info.get('powIIPId')
            powiat_nazwa = powiat_info.get('powNazwa')
            powiaty_dict[powiat_nazwa] = powiat_id
        return powiaty_dict
    else:
        print(f"Błąd: {response.status_code}")
        
    
def get_gminy(pow_id):
    url = f"http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/gmi/PL.PZGIK.200/{pow_id}/pel.json"
    response = requests.get(url)
    if response.status_code == 200:
        gminy = response.json()
        gminy_arr = []
        for gmina in gminy['jednAdms']:
            gmina_nazwa = gmina['jednAdm'].get('gmNazwa')
            gminy_arr.append(gmina_nazwa)
        return sorted(gminy_arr)
    else:
        print(f"Błąd: {response.status_code}")
        