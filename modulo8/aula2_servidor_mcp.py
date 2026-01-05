import logging
from mcp.server import FastMCP

logging.basicConfig(level=logging.WARNING)
logging.getLogger().setLevel(logging.WARNING)
logging.disable(logging.INFO)

mcp = FastMCP(
    name="Sevidor MCP OM"
)

@mcp.tool()
def calculadora_expressao(expressao: str) -> str:
    """
    Calcula expressões aritméticas com + - * / % ** e parênteses
    """
    try:
        result = eval(expressao)
    except Exception as e:
        return f'Não foi possivel executar a operação. Erro: {e}'
    return str(result)


if __name__ == "__main__":
    mcp.run()
