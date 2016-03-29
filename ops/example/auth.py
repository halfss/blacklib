AUTH_URL='http://localhost:5000/v2.0'
TENANT='admin'
USERNAME='halfss'
PASSWORD='halfss'
from keystoneclient.v2_0 import client
keystone = client.Client(username=USERNAME, password=PASSWORD, tenant_name=TENANT, auth_url=AUTH_URL)
print keystone.auth_token
