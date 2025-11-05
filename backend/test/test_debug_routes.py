def test_debug_list_routes(client):
    routes = [(r.path, sorted(getattr(r, "methods", []))) for r in client.app.routes]
    print("\nROUTES:", routes)
    assert routes  # al menos una