from datasette import hookimpl
from datasette.utils.asgi import Response
import llm
from datasette_llm_accountant import Accountant, Tx, LlmWrapper
from datasette_llm_accountant.pricing import nanocents_to_usd


class InMemoryAccountant(Accountant):
    """
    In-memory accountant that always approves requests and logs to datasette._llm_accountant_transactions.
    """

    def __init__(self, datasette):
        self.datasette = datasette
        # Initialize the transactions list if it doesn't exist
        if not hasattr(datasette, "_llm_accountant_transactions"):
            datasette._llm_accountant_transactions = []

    async def reserve(self, nanocents: int) -> Tx:
        """Always approve reservations."""
        tx_id = f"tx-{len(self.datasette._llm_accountant_transactions)}"
        return Tx(tx_id)

    async def settle(self, tx: Tx, nanocents: int):
        """Record the settled transaction."""
        self.datasette._llm_accountant_transactions.append({
            "tx_id": str(tx),
            "nanocents": nanocents,
            "usd": nanocents_to_usd(nanocents),
        })

    async def rollback(self, tx: Tx):
        """Rollback does nothing for this demo."""
        pass


@hookimpl
def register_llm_accountants(datasette):
    """Register the in-memory accountant."""
    return [InMemoryAccountant(datasette)]


async def llm_accountant_page(request, datasette):
    """Handle the /-/llm-accountant page."""

    # Initialize transactions list if needed
    if not hasattr(datasette, "_llm_accountant_transactions"):
        datasette._llm_accountant_transactions = []

    response_text = None
    error = None
    selected_model = None
    prompt_text = None

    # Get all available async models
    models = list(llm.get_async_models())

    # Handle form submission
    if request.method == "POST":
        formdata = await request.post_vars()
        selected_model = formdata.get("model")
        prompt_text = formdata.get("prompt")

        if selected_model and prompt_text:
            try:
                # Use the LlmWrapper to get the model with accounting
                wrapper = LlmWrapper(datasette)
                model = wrapper.get_async_model(selected_model)

                # Execute the prompt with default 50 cent reservation
                response_text = await model.prompt(prompt_text)

            except Exception as e:
                error = str(e)

    # Render the template
    return Response.html(
        await datasette.render_template(
            "llm_accountant.html",
            {
                "models": models,
                "selected_model": selected_model,
                "prompt_text": prompt_text,
                "response_text": response_text,
                "error": error,
                "transactions": datasette._llm_accountant_transactions,
            },
            request=request,
        )
    )


@hookimpl
def register_routes():
    """Register the /-/llm-accountant route."""
    return [
        (r"^/-/llm-accountant$", llm_accountant_page),
    ]
