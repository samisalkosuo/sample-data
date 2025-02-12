#start sqlserver and run it in background
/opt/mssql/bin/sqlservr & 

#setup sqlserver
/sqlserver/setup.sh

#sleep to keep container running
exec /sqlserver/sleep.sh