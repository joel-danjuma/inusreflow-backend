from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    brokers,
    commission_configs,
    installments,
    insurance_companies,
    payments,
    payments_bulk,
    policies,
    policyholders,
    reminders,
    settlements,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(insurance_companies.router)
api_router.include_router(brokers.router)
api_router.include_router(policyholders.router)
api_router.include_router(policies.router)
api_router.include_router(installments.router)
api_router.include_router(reminders.router)
api_router.include_router(commission_configs.router)
api_router.include_router(payments_bulk.router)
api_router.include_router(payments.router)
api_router.include_router(settlements.router)
api_router.include_router(webhooks.router)
