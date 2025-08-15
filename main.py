import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="SaaS Scout API", description="Compare pricing of popular SaaS providers")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ServiceTier(BaseModel):
    name: str
    price: str
    features: List[str]

class SaasService(BaseModel):
    id: str
    name: str
    category: str
    description: str
    tiers: List[ServiceTier]
    advantages: List[str]
    disadvantages: List[str]
    link: str
    logo_url: Optional[str] = None

# Your full SAAS_SERVICES list goes here (unchanged from your provided code)
# ------------------------------
SAAS_SERVICES = [
    # ... same list you provided above ...
]
# ------------------------------

@app.get("/")
async def root():
    return {"message": "SaaS Scout API - Compare pricing of popular SaaS providers", "version": "2.0", "services_count": len(SAAS_SERVICES)}

@app.get("/api/services", response_model=List[SaasService])
async def get_services(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc"
):
    services = SAAS_SERVICES.copy()
    
    if category and category.lower() != "all":
        services = [s for s in services if s["category"].lower() == category.lower()]
    
    if search:
        search_lower = search.lower()
        services = [
            s for s in services 
            if search_lower in s["name"].lower() 
            or search_lower in s["description"].lower()
            or any(search_lower in adv.lower() for adv in s["advantages"])
        ]
    
    if sort_by == "name":
        services.sort(key=lambda x: x["name"].lower(), reverse=(sort_order == "desc"))
    elif sort_by == "category":
        services.sort(key=lambda x: x["category"].lower(), reverse=(sort_order == "desc"))
    elif sort_by == "price":
        def extract_price(service):
            first_tier_price = service["tiers"][0]["price"]
            if "₹0" in first_tier_price or "Free" in first_tier_price:
                return 0
            elif "Custom" in first_tier_price:
                return 999999
            else:
                import re
                numbers = re.findall(r'[\d,]+', first_tier_price.replace(',', ''))
                return int(numbers[0]) if numbers else 999999
        services.sort(key=extract_price, reverse=(sort_order == "desc"))
    
    return services

@app.get("/api/services/{service_id}", response_model=SaasService)
async def get_service(service_id: str):
    service = next((s for s in SAAS_SERVICES if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@app.get("/api/categories")
async def get_categories():
    categories = list(set(service["category"] for service in SAAS_SERVICES))
    return {"categories": sorted(categories)}

@app.get("/api/cheapest")
async def get_cheapest_by_category():
    from collections import defaultdict
    cheapest_by_category = defaultdict(lambda: {"service": None, "price": float('inf')})
    for service in SAAS_SERVICES:
        category = service["category"]
        first_tier = service["tiers"][0]
        price_str = first_tier["price"]
        if "₹0" in price_str or "Free" in price_str:
            price = 0
        elif "Custom" in price_str:
            continue
        else:
            import re
            numbers = re.findall(r'[\d,]+', price_str.replace(',', ''))
            price = int(numbers[0]) if numbers else float('inf')
        if price < cheapest_by_category[category]["price"]:
            cheapest_by_category[category] = {
                "service": service,
                "price": price,
                "tier": first_tier
            }
    return dict(cheapest_by_category)

# Railway port binding
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
