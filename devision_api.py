import requests

def get_wojewodztwa():
    url = "http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/woj.json"
    response = requests.get(url)

    if response.status_code == 200:
        wojewodztwa = response.json()
        return wojewodztwa
    else:
        print(f"Błąd: {response.status_code}")
        return None


def get_powiaty(woj_id):
    url = f"http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/pow/PL.PZGIK.200/{woj_id}/skr.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        powiaty = response.json()
        return powiaty
    else:
        print(f"Błąd: {response.status_code}")
        return None
    
def get_gminy(pow_id):
    url = f"http://mapy.geoportal.gov.pl/wss/service/SLN/guest/sln/gmi/PL.PZGIK.200/{pow_id}/pel.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        gminy = response.json()
        return gminy
    else:
        print(f"Błąd: {response.status_code}")
        return None

def make_administrative_devision_dict():
    devision_dict = {}

    for wojewodztwo in get_wojewodztwa().get('jednAdms', []):
        wojewodztwo_info = wojewodztwo.get('jednAdm')
        wojewodztwo_id = wojewodztwo_info.get('wojIIPId')
        wojewodztwo_nazwa = wojewodztwo_info.get('wojNazwa')
        devision_dict[wojewodztwo_nazwa] = {}
        print(wojewodztwo_nazwa)
        
        for powiat in get_powiaty(wojewodztwo_id).get('jednAdms'):
            powiat_info = powiat.get('jednAdm')
            powiat_id = powiat_info.get('powIIPId')
            powiat_nazwa = powiat_info.get('powNazwa')
            devision_dict[wojewodztwo_nazwa][powiat_nazwa] = []
            #print(powiat_nazwa)

            for gmina in get_gminy(powiat_id).get('jednAdms'):
                devision_dict[wojewodztwo_nazwa][powiat_nazwa].append(gmina.get('jednAdm').get('gmNazwa'))
                #print(gmina.get('jednAdm').get('gmNazwa'))

    print('\n\n\n') 
    print(devision_dict)


#print(get_gminy('1846e6d9-3e9c-4328-a203-d6d4ccd61aa2'))

make_administrative_devision_dict()