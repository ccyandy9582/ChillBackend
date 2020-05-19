import mysql
# import mysql.connector
# from dotevn import load_dotenv, find_dotenv


class Connector():
    def __init__(self):
        self._host = "hotrip.cftxv1tfg8he.us-east-1.rds.amazonaws.com"
        self._username = "chilladmin"
        self._password = "ChillPa$$w0rd"
        self._database = "hochilltrip"

    def createConnection(self):
        cnx = mysql.connector.Connect(host=self._host,
                                      user=self._username,
                                      passwd=self._password,
                                      database=self._database)
        return cnx

    # dotevnPath = join(dirname(__file__), '.env')
    # load_dotenv(dotevnPath, override=True)
    # googleMapKey = os.environ.get("googleMapKey")
