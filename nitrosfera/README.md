# Logo Nitrosfera – modelo 3D para Flashforge AD5X

Disco redondo de **200 mm de diâmetro × 30 mm de espessura**, com corte plano embaixo
(base de ~78 mm) para ficar em pé. Altura final: 192 mm. Cabe na mesa 220×220 da AD5X.

## Arquivos
| Arquivo | Uso |
|---|---|
| `nitrosfera_3cores.3mf` | Versão colorida (vermelho, preto, branco) – um objeto com 3 partes |
| `nitrosfera_cor_vermelho.stl` / `_preto.stl` / `_branco.stl` | As mesmas 3 partes separadas |
| `nitrosfera_1cor_relevo.stl` | Versão de 1 cor: anel e ponteiro em relevo de 2 mm |
| `preview_frente.png` | Vista frontal |

O corpo é vermelho. O anel preto e o fundo branco são uma camada de 1,2 mm embutida
no topo, então a troca de cor só acontece nas últimas 6 camadas.

## Como fatiar (Orca-Flashforge)
1. Abra `nitrosfera_3cores.3mf`. Se aparecer como 3 objetos soltos, apague-os e importe os
   3 STLs de cor **juntos**, respondendo **Sim** para "carregar como um único objeto com várias partes".
2. Na lista de objetos, atribua: vermelho → filamento 1, preto → 2, branco → 3.
3. Imprima **deitado, com a logo para cima** (já vem assim). Sem suportes.
4. Sugestão: altura de camada 0,2 mm, 3 paredes, 5 camadas no topo, 15% de preenchimento giroide,
   ironing no topo para a face ficar lisa.

Gerado por `gerar_modelo.py` (`python3 gerar_modelo.py logo_original.jpg .`).
