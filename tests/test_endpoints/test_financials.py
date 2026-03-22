from __future__ import annotations


INCOME_STMT = [
    {
        "date": "2023-09-30",
        "symbol": "AAPL",
        "revenue": 383285000000,
        "netIncome": 96995000000,
        "period": "FY",
    }
]


def test_income_statement(client, httpx_mock):
    httpx_mock.add_response(json=INCOME_STMT)
    result = client.income_statement("AAPL")
    assert result[0]["revenue"] == 383285000000


def test_income_statement_quarterly(client, httpx_mock):
    httpx_mock.add_response(json=INCOME_STMT)
    result = client.income_statement("AAPL", period="quarter", limit=4)
    req = httpx_mock.get_requests()[0]
    assert "period=quarter" in str(req.url)
    assert "limit=4" in str(req.url)


def test_balance_sheet(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "totalAssets": 352583000000}])
    result = client.balance_sheet("AAPL")
    assert result[0]["totalAssets"] == 352583000000


def test_cash_flow(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "operatingCashFlow": 110543000000}])
    result = client.cash_flow_statement("AAPL")
    assert result[0]["operatingCashFlow"] == 110543000000


def test_key_metrics(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "peRatio": 27.78}])
    result = client.key_metrics("AAPL")
    assert result[0]["peRatio"] == 27.78


def test_ratios(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "currentRatio": 0.99}])
    result = client.ratios("AAPL")
    assert result[0]["currentRatio"] == 0.99


def test_financial_scores(client, httpx_mock):
    httpx_mock.add_response(json=[{"symbol": "AAPL", "altmanZScore": 8.5}])
    result = client.financial_scores("AAPL")
    assert result[0]["altmanZScore"] == 8.5
