from .session import NanoSession

class NanoRouter:
    def __init__(self, delimiter: str="/") -> None:
        self.delimiter: str = str(delimiter)
        self.routes: dict[str|int, dict[str, callable|dict]] = {} # route/routeID: {hook: NanoHook, args: {args...}}

    def register(self, route: str|int, hook: callable, args: dict) -> None:
        if self.routes.get(route, False) != False:
            print("OVERWRITING ROUTE:", route)
            return
        self.routes[route] = {"hook": hook, "args": args}
    
    def dispatch(self, request: dict, session: NanoSession) -> None:
        match request["proto"]:
            case "NPHS":
                _,__,___,method = request["meta"]
                route = self.routes.get(method, None)
                if route is None:
                    print(f"[NanoRouter] route not-registered: {method}")
                    return
                else:
                    if callable(route["hook"]): route["hook"](route["hook"], request, session, route["args"])
            case _:
                print(f"[NanoRouter] route not-registered: {method}")
                return
