from sanic import Sanic, response
from sanic.response import json
from sanic.request import Request
import aiomysql
import hashlib

app = Sanic("EmployeeRegistration")

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "port": 3306,
    "password": "@Ndikumana2608!",
    "db": "registration"
}

# Initialize a connection pool
@app.listener("before_server_start")
async def setup_db(app, loop):
    app.ctx.db_pool = await aiomysql.create_pool(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        db=db_config["db"],
        loop=loop,
        autocommit=True,
        minsize=1,
        maxsize=10
    )

@app.listener("after_server_stop")
async def close_db(app, _):
    app.ctx.db_pool.close()
    await app.ctx.db_pool.wait_closed()

@app.post("/register")
async def register_employee(request: Request):
    data = request.json

    # Validate role
    role = data.get("role")
    if role not in ["doctor", "nurse"]:
        return response.json({"error": "Invalid role. Must be 'doctor' or 'nurse'."}, status=400)

    # Validate required fields
    Employee_name = data.get("Employee_name")
    surname = data.get("surname")
    email = data.get("email")
    gender = data.get("gender")
    contacts = data.get("contacts")
    Employee_password = data.get("Employee_password")
    department = data.get("department")

    missing_fields = [field for field in ["Employee_name", "surname", "email", "gender", "contacts", "department"] if not data.get(field)]
    if missing_fields:
        return response.json({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=400)


    #if not all([Employee_name, surname, email, gender, contacts,department]):
        #return response.json({"error": "Missing required fields: name, surname, email, gender, contacts,department."}, status=400) #add employee_department

    if role in ["doctor", "nurse"] and not Employee_password:
        return response.json({"error": "Password is required for doctors and nurses."}, status=400)

    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Insert into employees table
                await cursor.execute(
                    "INSERT INTO employees (Employee_name, surname, email, gender, contacts,department) VALUES (%s, %s, %s, %s, %s, %s)",#add employee_department
                    (Employee_name, surname, email, gender, contacts,department)#add employee_department
                )
                employee_id = cursor.lastrowid  # Get the last inserted ID

                # Insert into specific role table with password and degree
                if role == "doctor":
                    degree = data.get("degree")
                    specialization = data.get("specialization")

                    # Hash the password
                    hashed_password = hashlib.sha256(Employee_password.encode('utf-8')).hexdigest()
                    await cursor.execute(
                        "INSERT INTO doctors (id, degree, specialization, Employee_password) VALUES (%s, %s, %s, %s)",
                        (employee_id, degree, specialization, hashed_password)
                    )

                elif role == "nurse":
                    degree = data.get("degree")

                    # Hash the password
                    hashed_password = hashlib.sha256(Employee_password.encode('utf-8')).hexdigest()
                    await cursor.execute(
                        "INSERT INTO nurses (id, degree, Employee_password) VALUES (%s, %s, %s)",
                        (employee_id, degree, hashed_password)
                    )

                return response.json({"message": f"{role.capitalize()} registered successfully", "id": employee_id})

    except aiomysql.MySQLError as e:
        print(f"Database error: {e}")
        return response.json({"error": "Database operation failed. Please try again."}, status=500)

    except Exception as e:
        print(f"Unexpected error: {e}")
        return response.json({"error": "An unexpected error occurred. Please try again."}, status=500)
    
@app.put("/update/employee/<id:int>")
async def update_employee(request, id):
    data = request.json
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if employee exists
                await cursor.execute("SELECT * FROM employees WHERE id = %s", (id,))
                employee = await cursor.fetchone()
                if not employee:
                    return json({"error": "Employee not found."}, status=404)

                # Update general employee details
                update_fields = ", ".join([f"{key} = %s" for key in data.keys()])
                await cursor.execute(
                    f"UPDATE employees SET {update_fields} WHERE id = %s",
                    (*data.values(), id)
                )
                return json({"message": "Employee details updated successfully."})
    except Exception as e:
        return json({"error": str(e)}, status=500)

@app.put("/update/doctor/<id:int>")
async def update_doctor(request, id):
    data = request.json
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if doctor exists
                await cursor.execute("SELECT * FROM doctors WHERE id = %s", (id,))
                doctor = await cursor.fetchone()
                if not doctor:
                    return json({"error": "Doctor not found."}, status=404)

                # Hash password if provided
                if "Employee_password" in data:
                    data["Employee_password"] = hashlib.sha256(
                        data["Employee_password"].encode("utf-8")
                    ).hexdigest()

                # Update doctor details
                update_fields = ", ".join([f"{key} = %s" for key in data.keys()])
                await cursor.execute(
                    f"UPDATE doctors SET {update_fields} WHERE id = %s",
                    (*data.values(), id)
                )
                return json({"message": "Doctor details updated successfully."})
    except Exception as e:
        return json({"error": str(e)}, status=500)

@app.put("/update/nurse/<id:int>")
async def update_nurse(request, id):
    data = request.json
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if nurse exists
                await cursor.execute("SELECT * FROM nurses WHERE id = %s", (id,))
                nurse = await cursor.fetchone()
                if not nurse:
                    return json({"error": "Nurse not found."}, status=404)

                # Hash password if provided
                if "Employee_password" in data:
                    data["Employee_password"] = hashlib.sha256(
                        data["Employee_password"].encode("utf-8")
                    ).hexdigest()

                # Update nurse details
                update_fields = ", ".join([f"{key} = %s" for key in data.keys()])
                await cursor.execute(
                    f"UPDATE nurses SET {update_fields} WHERE id = %s",
                    (*data.values(), id)
                )
                return json({"message": "Nurse details updated successfully."})
    except Exception as e:
        return json({"error": str(e)}, status=500)

@app.delete("/delete/employee/<id:int>")
async def delete_employee(request, id):
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if employee exists
                await cursor.execute("SELECT * FROM employees WHERE id = %s", (id,))
                employee = await cursor.fetchone()
                if not employee:
                    return json({"error": "Employee not found."}, status=404)

                # Delete associated doctor or nurse entry if exists
                await cursor.execute("DELETE FROM doctors WHERE id = %s", (id,))
                await cursor.execute("DELETE FROM nurses WHERE id = %s", (id,))

                # Delete employee entry
                await cursor.execute("DELETE FROM employees WHERE id = %s", (id,))
                return json({"message": "Employee deleted successfully."})
    except Exception as e:
        return json({"error": str(e)}, status=500)
@app.get("/view/employees")
async def view_employees(request):
    """
    Retrieve all employees.
    """
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Fetch all employees
                await cursor.execute("SELECT id, Employee_name, surname, email, gender, contacts,department FROM employees")#add employee_department
                employees = await cursor.fetchall()
                # Column names
                columns = ["id", "Employee_name", "surname", "email", "gender", "contacts","department"]#add employee_department
                # Format as list of dictionaries
                result = [dict(zip(columns, row)) for row in employees]
                return json(result)
    except Exception as e:
        return json({"error": str(e)}, status=500)

@app.get("/view/doctors")
async def view_doctors(request):
    """
    Retrieve all doctors with their associated employee details.
    """
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Fetch doctor details with corresponding employee data  #add employee_department #add employee_department
                await cursor.execute("""
                    SELECT e.id, e.Employee_name, e.surname, e.email, e.gender, e.contacts,e.department,   
                           d.degree, d.specialization,d.Employee_password
                    FROM employees e
                    INNER JOIN doctors d ON e.id = d.id
                """)
                doctors = await cursor.fetchall()
                # Column names #add employee_department
                columns = ["id", "Employee_name", "surname", "email", "gender", "contacts","department", "degree", "specialization","Employee_password"]
                # Format as list of dictionaries
                result = [dict(zip(columns, row)) for row in doctors]
                return json(result)
    except Exception as e:
        return json({"error": str(e)}, status=500)

@app.get("/view/nurses")
async def view_nurses(request):
    """
    Retrieve all nurses with their associated employee details.
    """
    try:
        async with app.ctx.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Fetch nurse details with corresponding employee data #add employee_department #add employee_department
                await cursor.execute("""
                    SELECT e.id, e.Employee_name, e.surname, e.email, e.gender, e.contacts,e.department,
                           n.degree,n.Employee_password
                    FROM employees e
                    INNER JOIN nurses n ON e.id = n.id
                """)
                nurses = await cursor.fetchall()
                # Column names
                columns = ["id", "Employee_name", "surname", "email", "gender", "contacts","department", "degree","Employee_password"]
                # Format as list of dictionaries
                result = [dict(zip(columns, row)) for row in nurses]
                return json(result)
    except Exception as e:
        return json({"error": str(e)}, status=500)


@app.get("/test")
async def test_route(request):
    return json({"message": "Server is running!"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001)
