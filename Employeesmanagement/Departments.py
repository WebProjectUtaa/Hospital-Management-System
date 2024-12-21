from sanic import Sanic, response
import aiomysql

# Initialize the Sanic app
app = Sanic("DepartmentApp")

# Setup database configuration
db_config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "@Ndikumana2608!",
    "db": "registration",
}

# Database connection helper function
async def get_connection():
    return await aiomysql.connect(**db_config)

@app.post("/departments")
async def create_department(request):
    data = request.json
    department_id = data.get("department_id")
    department_name = data.get("department_name")
    employee_id = data.get("id")  # Employee ID is stored as `id` in your database.

    if not department_name or not employee_id or not department_id:
        return response.json({"error": "department_name, id, and department_id are required."}, status=400)

    try:
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check if the employee exists
                await cur.execute("SELECT id FROM employees WHERE id=%s", (employee_id,))
                employee = await cur.fetchone()
                if not employee:
                    return response.json({"error": "Employee does not exist."}, status=404)

                # Insert the department
                await cur.execute(
                    """
                    INSERT INTO departments (department_id, department_name, id)
                    VALUES (%s, %s, %s)
                    """,
                    (department_id, department_name, employee_id)
                )
                await conn.commit()
                return response.json({"message": "Department created successfully."}, status=201)
    except Exception as e:
        print(f"Error: {e}")  # Log the actual error to the console
        return response.json({"error": "Failed to create department."}, status=500)


# Route to fetch all departments
@app.get("/departments")
async def get_departments(request):
    try:
        async with await get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM departments")
                departments = await cur.fetchall()
                return response.json(departments)
    except Exception as e:
        return response.json({"error": "Failed to fetch departments."}, status=500)

# Route to update a department's details
@app.put("/departments/<department_id:int>")
async def update_department(request, department_id):
    data = request.json
    department_name = data.get("department_name")
    employee_id = data.get("id")

    try:
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check if the department exists
                await cur.execute("SELECT * FROM departments WHERE department_id=%s", (department_id,))
                department = await cur.fetchone()
                if not department:
                    return response.json({"error": "Department does not exist."}, status=404)

                # Update the department
                await cur.execute(
                    """
                    UPDATE departments
                    SET department_name=%s, id=%s
                    WHERE department_id=%s
                    """,
                    (department_name,id, department_id)
                )
                await conn.commit()
                return response.json({"message": "Department updated successfully."})
    except Exception as e:
        return response.json({"error": "Failed to update department."}, status=500)

# Route to delete a department
@app.delete("/departments/<department_id:int>")
async def delete_department(request, department_id):
    try:
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check if the department exists
                await cur.execute("SELECT * FROM departments WHERE department_id=%s", (department_id,))
                department = await cur.fetchone()
                if not department:
                    return response.json({"error": "Department does not exist."}, status=404)

                # Delete the department
                await cur.execute("DELETE FROM departments WHERE department_id=%s", (department_id,))
                await conn.commit()
                return response.json({"message": "Department deleted successfully."})
    except Exception as e:
        return response.json({"error": "Failed to delete department."}, status=500)

# Run the app
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
