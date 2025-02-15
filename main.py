import os
import json
import random
import threading
import time
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
import uvicorn
import schedule
import starkbank
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar variáveis de ambiente
private_key_content = os.environ.get("PRIVATE_KEY")
project_id = os.environ.get("STARKBANK_PROJECT_ID")

user = starkbank.Project(
    environment="sandbox",
    id=project_id,
    private_key=private_key_content
)
starkbank.user = user

# TARGET_ACCOUNT via variável de ambiente (JSON)
TARGET_ACCOUNT = json.loads(os.environ.get("TARGET_ACCOUNT",
                                           '{"bank_code": "20018183","branch_code": "0001","account_number": "6341320293482496","name": "Stark Bank S.A.","tax_id": "20.018.183/0001-80","account_type": "payment"}'))

NAMES = [
    "Tony Stark", "Peter Parker", "Bruce Wayne", "Clark Kent", "Diana Prince",
    "Natasha Romanoff", "Steve Rogers", "Wanda Maximoff", "Scott Lang", "T'Challa"
]


def generate_valid_cpf():
    digits = [random.randint(0, 9) for _ in range(9)]
    sum_val = sum((10 - i) * digits[i] for i in range(9))
    remainder = sum_val % 11
    d1 = 0 if remainder < 2 else 11 - remainder
    digits.append(d1)
    sum_val = sum((11 - i) * digits[i] for i in range(10))
    remainder = sum_val % 11
    d2 = 0 if remainder < 2 else 11 - remainder
    digits.append(d2)
    return "".join(str(d) for d in digits)


def create_invoice(amount, name, tax_id, due):
    invoice = starkbank.Invoice(
        amount=amount,
        name=name,
        tax_id=tax_id,
        due=due,
        expiration=5097600,
        fine=2.0,
        interest=1.0,
        tags=["auto-generated"]
    )
    return invoice


def issue_invoices():
    num_invoices = random.randint(8, 12)
    invoices = []
    for _ in range(num_invoices):
        amount = random.randint(1000, 100000)
        name = random.choice(NAMES)
        tax_id = generate_valid_cpf()
        due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        invoices.append(create_invoice(amount, name, tax_id, due))
    try:
        created_invoices = starkbank.invoice.create(invoices)
        for inv in created_invoices:
            logger.info(f"Invoice criada: ID {inv.id} | Valor: {inv.amount} centavos | Cliente: {inv.name}")
    except Exception as e:
        logger.error(f"Erro ao criar invoices: {e}")


def run_scheduler():
    schedule.every(3).hours.do(issue_invoices)
    issue_invoices()  # Emite imediatamente
    start_time = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - start_time) < timedelta(hours=24):
        schedule.run_pending()
        time.sleep(1)
    logger.info("Encerrando emissão de invoices após 24 horas.")


def send_transfer(net_amount):
    try:
        transfers = starkbank.transfer.create([
            starkbank.Transfer(
                amount=net_amount,
                tax_id=TARGET_ACCOUNT["tax_id"],
                name=TARGET_ACCOUNT["name"],
                bank_code=TARGET_ACCOUNT["bank_code"],
                branch_code=TARGET_ACCOUNT["branch_code"],
                account_number=TARGET_ACCOUNT["account_number"],
                account_type=TARGET_ACCOUNT["account_type"],
            )
        ])
        transfer = transfers[0]
        logger.info(f"Transfer realizado: ID {transfer.id} | Valor: {net_amount} centavos")
    except Exception as e:
        logger.error(f"Erro ao criar transfer: {e}")


app = FastAPI()


@app.on_event("startup")
def startup_event():
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


@app.post("/webhook/invoice")
async def invoice_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Erro ao ler JSON: {e}")
        return {"status": "erro", "message": "JSON inválido"}

    logger.info(f"[{datetime.now(timezone.utc)}] Webhook recebido: {payload}")

    event = payload.get("event")
    if event:
        log = event.get("log", {})
        if log.get("type") == "credited" and log.get("invoice"):
            invoice_data = log["invoice"]
            amount = invoice_data.get("amount", 0)
            fee = invoice_data.get("fee", 0)
            net_amount = amount - fee
            logger.info(f"Invoice creditada: amount={amount}, fee={fee} -> net={net_amount}")
            send_transfer(net_amount)
        else:
            logger.info("Evento não processado (tipo diferente ou dados incompletos).")
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
