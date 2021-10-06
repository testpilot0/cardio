import plivo
auth_id = ‘Your AUTH ID’
auth_token = ‘Your AUTH Token’
phlo_id = ‘Your PHLO ID’ # https://console.plivo.com/phlo/list/
phlo_client = plivo.phlo.RestClient(auth_id=auth_id, auth_token=auth_token)
phlo = phlo_client.phlo.get(phlo_id)
response = phlo.run()
print str(response)
