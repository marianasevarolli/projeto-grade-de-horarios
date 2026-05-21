import sys
import os

# Adiciona a pasta raiz ao path para importar o projeto.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from projeto import validar_capacidade, validar_tipo_sala, validar_habilitacao

def testar_regra_capacidade():
    print("Testando Regra de Capacidade...")
    turma_grande = {'alunos': 50}
    sala_pequena = {'capacidade': 30}
    
    assert validar_capacidade(turma_grande, sala_pequena) == False
    print("✅ Teste de capacidade: OK (Barrou turma maior que a sala)")

def testar_regra_tipo_sala():
    print("Testando Regra de Correspondência Exata de Sala...")
    
    turma_lab = {'tipo': 'Laboratório'}
    sala_teorica = {'tipo': 'Teórica'}
    
    turma_teorica = {'tipo': 'Teórica'}
    sala_lab = {'tipo': 'Laboratório'}
    
    # 1. Tentar colocar Lab em Teórica (Deve ser False)
    assert validar_tipo_sala(turma_lab, sala_teorica) == False
    
    # 2. Tentar colocar Teórica em Lab (Deve ser False)
    assert validar_tipo_sala(turma_teorica, sala_lab) == False
    
    print("✅ Teste de tipo de sala: OK (Bloqueou cruzamentos incorretos)")

def testar_regra_habilitacao():
    print("Testando Regra de Habilitação...")
    professor = {'disciplina': 'História'}
    turma = {'disciplina': 'Cálculo'}
    
    assert validar_habilitacao(professor, turma) == False
    print("✅ Teste de habilitação: OK (Barrou professor em disciplina errada)")

if __name__ == "__main__":
    try:
        testar_regra_capacidade()
        testar_regra_laboratorio()
        testar_regra_habilitacao()
        print("\n🚀 Sucesso: Todos os testes de Regras de Negócio passaram!")
    except AssertionError:
        print("\n❌ Erro: Uma regra de negócio não está sendo respeitada pelo código.")


