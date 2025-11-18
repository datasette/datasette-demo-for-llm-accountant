from datasette.app import Datasette
import pytest


@pytest.mark.asyncio
async def test_plugin_is_installed():
    datasette = Datasette(memory=True)
    response = await datasette.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-demo-for-llm-accountant" in installed_plugins


@pytest.mark.asyncio
async def test_llm_accountant_page_loads():
    """Test that the /-/llm-accountant page loads."""
    datasette = Datasette(memory=True)
    response = await datasette.client.get("/-/llm-accountant")
    assert response.status_code == 200
    assert b"LLM Accountant Demo" in response.content
    assert b"Select Model:" in response.content


@pytest.mark.asyncio
async def test_accountant_is_registered():
    """Test that the in-memory accountant is registered."""
    from datasette_llm_accountant import LlmWrapper

    datasette = Datasette(memory=True)
    wrapper = LlmWrapper(datasette)
    accountants = wrapper._get_accountants()

    # Should have our InMemoryAccountant
    assert len(accountants) > 0
    assert accountants[0].__class__.__name__ == "InMemoryAccountant"


@pytest.mark.asyncio
async def test_transactions_list_initialized():
    """Test that transactions list is initialized."""
    datasette = Datasette(memory=True)

    # Access the page to trigger initialization
    await datasette.client.get("/-/llm-accountant")

    # Check that the transactions list exists
    assert hasattr(datasette, "_llm_accountant_transactions")
    assert isinstance(datasette._llm_accountant_transactions, list)


@pytest.mark.asyncio
async def test_csrf_token_present():
    """Test that CSRF token is present in the form."""
    datasette = Datasette(memory=True)
    response = await datasette.client.get("/-/llm-accountant")
    assert response.status_code == 200

    # Check that the CSRF token hidden input is present
    assert b'<input type="hidden" name="csrftoken"' in response.content
    assert b'value="' in response.content
