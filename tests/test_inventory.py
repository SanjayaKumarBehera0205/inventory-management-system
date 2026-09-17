def test_authentication(client):
    response = client.post("/api/v1/auth/register", json={"name": "Sanjaya", "email": "sanjaya@example.com", "password": "strongpass123"})
    assert response.status_code == 201
    assert client.get("/api/v1/products").status_code == 401


def test_product_and_stock_flow(client, auth):
    category = client.post("/api/v1/categories", headers=auth, json={"name": "Electronics"}).json()
    supplier = client.post("/api/v1/suppliers", headers=auth, json={"name": "Acme Supply", "email": "sales@acme.com"}).json()
    created = client.post(
        "/api/v1/products",
        headers=auth,
        json={"sku": "LAP-001", "name": "Laptop", "price": "999.99", "quantity": 10, "reorder_level": 3, "category_id": category["id"], "supplier_id": supplier["id"]},
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    movement = client.post("/api/v1/stock-movements", headers=auth, json={"product_id": product_id, "type": "stock_out", "quantity": 4, "note": "Customer order"})
    assert movement.status_code == 201
    assert movement.json()["new_quantity"] == 6
    assert client.get(f"/api/v1/products/{product_id}", headers=auth).json()["quantity"] == 6


def test_insufficient_stock_is_rejected(client, auth):
    product = client.post("/api/v1/products", headers=auth, json={"sku": "ITEM-1", "name": "Item", "price": "10.00", "quantity": 2}).json()
    response = client.post("/api/v1/stock-movements", headers=auth, json={"product_id": product["id"], "type": "stock_out", "quantity": 3})
    assert response.status_code == 400


def test_low_stock_and_dashboard(client, auth):
    client.post("/api/v1/products", headers=auth, json={"sku": "LOW-1", "name": "Low Item", "price": "25.00", "quantity": 2, "reorder_level": 5})
    low_stock = client.get("/api/v1/products?low_stock=true", headers=auth).json()
    assert low_stock["total"] == 1
    dashboard = client.get("/api/v1/dashboard", headers=auth)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_inventory_value"] == "50.00"


def test_duplicate_sku_is_rejected(client, auth):
    payload = {"sku": "SAME-1", "name": "Product", "price": "5.00"}
    assert client.post("/api/v1/products", headers=auth, json=payload).status_code == 201
    assert client.post("/api/v1/products", headers=auth, json=payload).status_code == 409
