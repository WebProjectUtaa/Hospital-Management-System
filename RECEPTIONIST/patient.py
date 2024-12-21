from sanic import Sanic
from sanic.response import json
import aiomysql
import hashlib

app = Sanic("PatientManagementSystem")

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",  
    "password": "@Ndikumana2608!",  
    "db": "registration",  
}

# Function to hash passwords
def hash_password(password):
    """
    Hashes a password using SHA-256.
    """
    return hashlib.sha256(password.encode()).hexdigest()

# Function to establish a database connection
async def get_db_connection():
    """
    Establishes a connection to the database.
    """
    return await aiomysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
    )

# Register patients
@app.post("/register")
async def register_patients(request):
    """
    Endpoint to register a new patient.
    """
    data = request.json
    required_fields = [
        "patient_name", "patient_surname", "patient_age", "patient_blood_group",
        "Gender", "contacts", "next_of_keen_contacts", "insurance", "patient_email", "password"
    ]

    # Validate request payload
    if not all(field in data for field in required_fields):
        return json({"error": "Missing required fields"}, status=400)

    # Hash the password
    hashed_password = hash_password(data["password"])

    # Insert patient data into the database
    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO patients (
                        patient_name, patient_surname, patient_age, patient_blood_group,
                        Gender, contacts, next_of_keen_contacts, insurance, patient_email, password
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data["patient_name"],
                        data["patient_surname"],
                        data["patient_age"],
                        data["patient_blood_group"],
                        data["Gender"],
                        data["contacts"],
                        data["next_of_keen_contacts"],
                        data["insurance"],
                        data["patient_email"],
                        hashed_password
                    )
                )
                await conn.commit()
        pool.close()
        await pool.wait_closed()

        return json({"message": "Patient registered successfully!"})

    except Exception as e:
        return json({"error": str(e)}, status=500)

# Update patient details
@app.route("/update/<patient_id:int>", methods=["PUT"])
async def update_patient(request, patient_id):
    """
    Endpoint to update patient details.
    """
    data = request.json

    try:
        conn = await get_db_connection()
        async with conn.cursor() as cur:
            # Check if the patient exists
            await cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            patient = await cur.fetchone()
            if not patient:
                return json({"error": "Patient not found"}, status=404)

            # Update patient details
            update_fields = ", ".join([f"{key} = %s" for key in data.keys()])
            query = f"UPDATE patients SET {update_fields} WHERE patient_id = %s"
            await cur.execute(query, (*data.values(), patient_id))
            await conn.commit()
        conn.close()
        return json({"message": "Patient updated successfully"}, status=200)

    except Exception as e:
        return json({"error": str(e)}, status=500)

# Delete a patient
@app.route("/delete/<patient_id:int>", methods=["DELETE"])
async def delete_patient(request, patient_id):
    """
    Endpoint to delete a patient by ID.
    """
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cur:
            # Check if the patient exists
            await cur.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            patient = await cur.fetchone()
            if not patient:
                return json({"error": "Patient not found"}, status=404)

            # Delete the patient record
            await cur.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
            await conn.commit()
        conn.close()
        return json({"message": "Patient deleted successfully"}, status=200)

    except Exception as e:
        return json({"error": str(e)}, status=500)

# View all patients
@app.route("/viewpatients")
async def view_patients(request):
    """
    Endpoint to retrieve all patients from the database.
    """
    conn = await get_db_connection()
    async with conn.cursor() as cur:
        # Query to fetch all patients
        await cur.execute("SELECT * FROM patients")
        patients = await cur.fetchall()

        # Column names for formatting the response
        columns = [
            "patient_id","patient_name", "patient_surname", "patient_age", "patient_blood_group",
            "Gender", "contacts", "next_of_keen_contacts", "insurance", "patient_email", "password"
        ]
        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in patients]
    
    conn.close()
    return json(result)

# Test route
@app.get("/test")
async def test_route(request):
    """
    Test route to check server status.
    """
    return json({"message": "Server is running!"})

# Run the application
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
