# Login route
@app.post("/login")
async def login(request):
    data = request.json
    email = data.get("email")
    password = data.get("password")

    async with await get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT id FROM patients WHERE email=%s AND password=%s", (email, password)
            )
            patient = await cursor.fetchone()

            if patient:
                return response.json({"message": "Login successful", "patient_id": patient[0]})
            return response.json({"message": "Invalid credentials"}, status=401)