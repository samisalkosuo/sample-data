#from: https://github.com/twright-msft/mssql-node-docker-demo-app

#run the setup script to create the DB and the schema in the DB
#do this in a loop because the timing for when the SQL instance is ready is indeterminate
for i in {1..50};
do
    /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P $MSSQL_SA_PASSWORD -d master -i setup.sql
    if [ $? -eq 0 ]
    then
        echo "setup.sql completed"
        break
    else
        #echo "setup not ready yet.."
        sleep 1
    fi
done

echo "Importing addresses..."
#sleep a moment before starting to import
sleep 5
/opt/mssql-tools18/bin/bcp demo.dbo.Addresses in "/sqlserver/addresses.csv" -c -t',' -u -S localhost -U sa -P $MSSQL_SA_PASSWORD
echo "Importing addresses...done."

echo "Importing professions..."
/opt/mssql-tools18/bin/bcp demo.dbo.Professions in "/sqlserver/professions.csv" -c -t',' -u -S localhost -U sa -P $MSSQL_SA_PASSWORD
echo "Importing professions...done."
