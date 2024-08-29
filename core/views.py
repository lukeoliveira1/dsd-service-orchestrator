import requests
from rest_framework import views
from rest_framework.response import Response


class PurchaseProductView(views.APIView):

    def post(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        # Verifica se a quantidade é um número inteiro
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"erro": "Quantidade inválida"}, status=400)

        # 1. Verificar disponibilidade do estoque no Inventory Service
        try:
            inventory_response = requests.get(
                f"http://localhost:8002/api/inventory/{product_id}"
            )
            inventory_response.raise_for_status()

            inventory_data = inventory_response.json()
            available_quantity = inventory_data.get("stock")

            if available_quantity is None:
                return Response(
                    {"erro": "Quantidade de estoque não disponível"}, status=400
                )
            if available_quantity < quantity:
                return Response({"erro": "Estoque insuficiente"}, status=400)

        except requests.RequestException:
            return Response(
                {"erro": "Falha ao verificar a disponibilidade do estoque"}, status=500
            )

        # 2. Criar o pedido no Product Service
        try:
            order_response = requests.post(
                "http://localhost:8001/api/orders/",
                json={"product_id": product_id, "quantity": quantity},
            )
            order_response.raise_for_status()

            order_data = order_response.json()
            order_id = order_data.get("order_id")

            if not order_id:
                return Response({"erro": "Falha ao criar o pedido"}, status=400)

        except requests.RequestException:
            return Response({"erro": "Falha ao criar o pedido"}, status=500)

        # 3. Reservar o inventário no Inventory Service
        try:
            inventory_reserve_response = requests.post(
                "http://localhost:8002/api/inventory/reserve/",
                json={"product_id": product_id, "quantity": quantity},
            )
            inventory_reserve_response.raise_for_status()

        except requests.RequestException:
            return Response({"erro": "Falha ao reservar o estoque"}, status=500)

        # 4. Processar o pagamento no Payment Service
        try:
            payment_response = requests.post(
                "http://localhost:8003/api/payment/",
                json={"order_id": order_id, "value": 100.00},
            )
            payment_response.raise_for_status()

        except requests.RequestException:
            # Tentar reverter o inventário no caso de falha no pagamento
            try:
                requests.put(
                    "http://localhost:8002/api/inventory/rollback/",
                    json={"product_id": product_id, "quantity": available_quantity},
                )
            except requests.RequestException:
                return Response(
                    {"erro": "Falha no pagamento e falha ao reverter o estoque"},
                    status=500,
                )

            return Response(
                {"erro": "Falha ao processar o pagamento. Estoque revertido."},
                status=500,
            )

        return Response({"status": "Compra Concluída"})
