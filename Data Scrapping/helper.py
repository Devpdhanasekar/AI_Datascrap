import psycopg2
def dbCommunication(query,insert=False):
    print("called")
    try:
        pgConnection = psycopg2.connect(
            host="localhost",
            database="postgres",
            port="5432",
            user="postgres",
            password="Devpds$3001"
        )
        pgConnection.autocommit = True
        cursor = pgConnection.cursor()
        print("Database connection successful")
        type(query)
        cursor.execute(query)
        if insert:
            return "Customer updated successfully" if query[0]=="u" else "Customer added successfully"
        print("Database query successful")
        data = cursor.fetchall()
        cursor.close()
        pgConnection.close()
        final_data = []
        for indivual in data:
            row={}
            for i,column in enumerate(cursor.description):
                row[column.name]=indivual[i]
            final_data.append(row)
        return final_data
    except Exception as e:
        print("Database connection failed",e)