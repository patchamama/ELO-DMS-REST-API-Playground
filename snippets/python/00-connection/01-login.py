# import the shared client:  from elo_playground import connect
# topic:    Log in and open a session
# category: Connection & session
# id:       connection.login

from elo_playground import connect

# connect(login=False) builds the client from ELOPG_* env vars but does
# NOT log in yet - so we can call login() ourselves and read the result.
elo = connect(login=False)

user = elo.login()                 # -> POST /rest/IXServicePortIF/login
print("logged in as:", user["name"], "(id " + str(user["id"]) + ")")
print("member of groups:", user.get("groupList"))

elo.close()                        # release the connection pool
