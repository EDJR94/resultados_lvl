import pandas as pd
import numpy as np
import inflection
import seaborn as sns
import plotly.express as px
import streamlit as st

st.set_page_config(layout='wide')



#======================================Loading Data========================#
path = 'data/order_export_2023-04-17.csv'
df_raw = pd.read_csv(path, encoding='ISO-8859-1')

#======================================Functions========================#
def df_mes_selecionado(df,mes):
  df_mes = df.loc[df3['data'].dt.month == mes,:]
  return df_mes

#======================================# 1.0 DATA DESCRIPTION========================#
df1 = df_raw.copy()
cols_new = list(map(lambda x: inflection.underscore(x), df1.columns))
df1.columns = cols_new
df1['data'] = pd.to_datetime(df1['data'])
df1['datahora'] = pd.to_datetime(df1['datahora'])

#======================================# 2.0 VARIABLE FILTERING========================#
df2 = df1.copy()
df2 = df2.loc[(df2['liquido'] != 0.0) & (df2['bruto'] != 0.0),:]
df2['lado'] = df2['lado'].apply(lambda x: 'Compra' if x == 'Venda' else 'Venda')
df2 = df2.assign(valor_por_contrato = df2['liquido'] / df2['quantidade'])
df2 = df2.loc[df2['duracao'] < 32000,:]
df2.reset_index(drop=True)
df2['ranking'] = 0
df2.loc[df2['liquido']>0,'ranking'] = 1
df2.loc[df2['liquido']<0,'ranking'] = -1
df2['valor_por_acao'] = df2['liquido']/(df2['preco']*df2['quantidade'])

#======================================#Visão Geral========================#
df3 = df2.copy()

#===============================================Streamlit Sidebar========================================


valor_inicial = st.sidebar.text_input("Data Inicial - YYYY-MM-DD")
valor_final = st.sidebar.text_input("Data Final - YYYY-MM-DD")

#valor_minimo = df3['data'].min().date()
#valor_maximo = df3['data'].max().date()
#valores_iniciais = (valor_minimo, valor_maximo)

#valores_selecionados = st.sidebar.slider("Selecione a data",valor_minimo, valor_maximo, valores_iniciais)
df3_mes = df3.loc[(df3['data'] >= pd.to_datetime(valor_inicial)) & (df3['data'] <= pd.to_datetime(valor_final))]
df3_mes.loc[:, 'codigo'] = df3_mes['codigo'].apply(lambda x: x[:3] if x.startswith(('WDO','WIN','DOL','IND','CCM')) else x)

#==========================###1.1 Abertura Futuros=================================================

#Todos os trades entre 09:00:00 e 09:10:00 dentro do mês
df3_hora_abertura_futuros = df3_mes.loc[(df3_mes['hora'] >= '09:00:00') & (df3_mes['hora'] <= '09:05:00'),:]

####1.1.1 Total Sala

df3_abertura_futuros_total = df3_hora_abertura_futuros.loc[:,['liquido','codigo']].groupby(['codigo']).sum().reset_index()
px.bar(df3_abertura_futuros_total,x='codigo',y='liquido', labels={'codigo':'Ativo','liquido':'Resultado Líquido'})


####1.1.2 Total por operador

df3_abertura_futuros_por_op = df3_hora_abertura_futuros.loc[:,['liquido','nome','codigo']].groupby(['nome','codigo']).sum().reset_index()


####1.1.3 Média Operações Vencedoras



op_vencedoras = df3_mes['liquido'] > 0
df3_vencedoras_media = df3_hora_abertura_futuros.loc[op_vencedoras,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_vencedoras_media.columns = ['codigo','media_melhores','qtd_melhores','melhor']


####1.1.4 Média Operações Perdedoras

op_perdedoras = df3_mes['liquido'] < 0
df3_perdedoras_media = df3_hora_abertura_futuros.loc[op_perdedoras,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','min']}).reset_index()
df3_perdedoras_media.columns = ['codigo','media_piores','qtd_piores','pior']


####1.1.5 Média de valor por pts

df3_media_p_contrato = df3_hora_abertura_futuros.loc[:,['valor_por_contrato','codigo']].groupby('codigo').mean().reset_index()

####1.1.6 Tempo Médio por Operação

df3_media_p_tempo = df3_hora_abertura_futuros.loc[:,['duracao','codigo']].groupby('codigo').mean().reset_index()
df3_media_p_tempo['duracao'] = round(df3_media_p_tempo['duracao'],2)


####1.1.7 Tabela final

df3_combinado = pd.merge(df3_abertura_futuros_total,df3_vencedoras_media, on='codigo')
df3_combinado1 = pd.merge(df3_combinado, df3_perdedoras_media, on='codigo')
df3_combinado2 = pd.merge(df3_combinado1,df3_media_p_contrato, on='codigo')
df3_combinado_ab_futuros = pd.merge(df3_combinado2,df3_media_p_tempo, on='codigo' )
nova_ordem_colunas = ['codigo','resultado','media_melhores','media_piores','melhor','pior','valor_por_contrato','qtd_melhores','qtd_piores','duracao']
df3_combinado_ab_futuros.reindex(columns=nova_ordem_colunas)
#Tabela Final
df3_combinado_ab_futuros['% vencedoras'] = round(df3_combinado_ab_futuros['qtd_melhores']/(df3_combinado_ab_futuros['qtd_melhores'] + df3_combinado_ab_futuros['qtd_piores']),2) 

#==========================###1.1 Futuros Tarde=================================================

#Todos os trades após 09:05:00 e 17:00:00
hora_tarde_futuros = (df3_mes['hora'] > '09:05:00') & (df3_mes['hora'] <= '17:00:00')
ativo_futuros = df3_mes['codigo'].str.startswith(('WDO','WIN','DOL','IND')) 

####1.2.1 Total Sala

df3_futuros_tarde = df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros),['liquido','codigo']].groupby(['codigo']).sum().reset_index()
df3_futuros_tarde['liquido'] = round(df3_futuros_tarde['liquido'],2)
#px.bar(df2_futuros_tarde,x='codigo',y='liquido', labels={'codigo':'Ativo','liquido':'Resultado Líquido'})


####1.2.2 Total por Operador

df3_tarde_futuros_op =  df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros),['liquido','nome','codigo']].groupby(['nome','codigo']).sum().reset_index()


####1.2.3 Média Operações Vencedoras

op_vencedoras = df3_mes['liquido'] > 0
df3_vencedoras_media_tarde = df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros) & (op_vencedoras),['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_vencedoras_media_tarde.columns = ['codigo','media_melhores','qtd_melhores','melhor']


####1.2.4 Média Op Perdedoras

op_perdedoras = df3_mes['liquido'] < 0
df3_perdedoras_media_tarde = df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros) & (op_perdedoras),['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','min']}).reset_index()
df3_perdedoras_media_tarde.columns = ['codigo','media_piores','qtd_piores','pior']


####1.2.5 Valor por contrato

df3_valor_p_contrato_tarde = df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros),['codigo','valor_por_contrato']].groupby('codigo').mean().reset_index()


####1.2.6 Tempo Operação

df3_tempo_op_tarde = df3_mes.loc[(hora_tarde_futuros) & (ativo_futuros),['codigo','duracao']].groupby('codigo').mean().reset_index()


####1.2.7 Tabela Final

df3_combinado = pd.merge(df3_futuros_tarde,df3_vencedoras_media_tarde, on='codigo')
df3_combinado1 = pd.merge(df3_combinado, df3_perdedoras_media_tarde, on='codigo')
df3_combinado2 = pd.merge(df3_combinado1,df3_valor_p_contrato_tarde, on='codigo')
df3_combinado_futuros_tarde = pd.merge(df3_combinado2,df3_tempo_op_tarde, on='codigo' )
nova_ordem_colunas = ['codigo','resultado','media_melhores','media_piores','melhor','pior','valor_por_contrato','qtd_melhores','qtd_piores','duracao']
df3_combinado_futuros_tarde.reindex(columns=nova_ordem_colunas)
#Tabela Final
df3_combinado_futuros_tarde['% vencedoras'] = round(df3_combinado_futuros_tarde['qtd_melhores']/(df3_combinado_futuros_tarde['qtd_melhores'] + df3_combinado_futuros_tarde['qtd_piores']),2) 


#==========================###1.1 Abertura Acoes=================================================

df3_hora_abertura_acoes = df3_mes.loc[(df3_mes['hora'] >= '10:00:00') & (df3_mes['hora'] < '12:00:00'),:]
df3_abertura_acoes = df3_hora_abertura_acoes.loc[~df3_hora_abertura_acoes['codigo'].str.startswith(('WDO','WIN','DOL','IND','CCM')),:]

####1.3.1 Total Sala

df3_total_ab_acoes = df3_abertura_acoes.loc[:,['liquido','codigo']].groupby('codigo').sum().reset_index().sort_values(by='liquido',ascending=False)
df3_total_ab_acoes['liquido'] = round(df3_total_ab_acoes['liquido'],2)


####1.3.2 Op Vencedoras

op_vencedoras = df3_abertura_acoes['liquido'] > 0
df3_vencedoras_ab_acoes = df3_abertura_acoes.loc[op_vencedoras,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_vencedoras_ab_acoes.columns = ['codigo','media_melhores','qtd_melhores','melhor']
df3_vencedoras_ab_acoes['media_melhores'] = round(df3_vencedoras_ab_acoes['media_melhores'],2)
df3_vencedoras_ab_acoes['melhor'] = round(df3_vencedoras_ab_acoes['melhor'],2)


####1.3.3 Op Perdedoras

op_perdedoras = df3_abertura_acoes['liquido'] < 0
df3_perdedoras_ab_acoes = df3_abertura_acoes.loc[op_perdedoras,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_perdedoras_ab_acoes.columns = ['codigo','media_piores','qtd_piores','pior']
df3_perdedoras_ab_acoes['media_piores'] = round(df3_perdedoras_ab_acoes['media_piores'],2)
df3_perdedoras_ab_acoes['pior'] = round(df3_perdedoras_ab_acoes['pior'],2)


####1.3.4 Valor por ação

#Fazer valor por ação(LOTE X PREÇO)
df3_valor_p_ab_acao = df3_abertura_acoes.loc[:,['codigo','valor_por_acao']].groupby('codigo').mean().reset_index().sort_values(by='valor_por_acao',ascending=False)
df3_valor_p_ab_acao['valor_por_acao'] = df3_valor_p_ab_acao['valor_por_acao']*100


####1.3.5 Tempo por Operação

df3_tempo_p_op_ab_acoes = df3_abertura_acoes.loc[:,['codigo','duracao']].groupby('codigo').mean().reset_index().sort_values(by='duracao',ascending=False)
df3_tempo_p_op_ab_acoes['duracao'] = round(df3_tempo_p_op_ab_acoes['duracao'],2)


####1.3.6 Tabela Final

df3_combinado = pd.merge(df3_total_ab_acoes,df3_vencedoras_ab_acoes, on='codigo')
df3_combinado1 = pd.merge(df3_combinado, df3_perdedoras_ab_acoes, on='codigo')
df3_combinado2 = pd.merge(df3_combinado1,df3_valor_p_ab_acao, on='codigo')
df3_combinado_ab_acoes = pd.merge(df3_combinado2,df3_tempo_p_op_ab_acoes, on='codigo' )
nova_ordem_colunas = ['codigo','liquido','media_melhores','media_piores','melhor','pior','valor_por_acao','qtd_melhores','qtd_piores','duracao']
df3_combinado_ab_acoes.reindex(columns=nova_ordem_colunas)
df3_combinado_ab_acoes['% vencedoras'] = round(df3_combinado_ab_acoes['qtd_melhores']/(df3_combinado_ab_acoes['qtd_melhores'] + df3_combinado_ab_acoes['qtd_piores']),2) 


#==========================###1.1 Leilao=================================================

df3_hora_leilao = df3_mes.loc[df3_mes['hora'] >= '15:00:00',:]
df3_hora_leilao = df3_hora_leilao.loc[~df3_hora_leilao['codigo'].str.startswith(('WDO','WIN','DOL','IND','CCM')),:]


####1.4.1 Total Sala

df3_total_leilao = df3_hora_leilao.loc[:,['liquido','codigo']].groupby('codigo').sum().reset_index().sort_values(by='liquido',ascending=False)
df3_total_leilao['liquido'] = round(df3_total_leilao['liquido'],2)


####1.4.2 Op Vencedoras

op_vencedoras_leilao = df3_hora_leilao['liquido'] > 0
df3_vencedoras_leilao = df3_hora_leilao.loc[op_vencedoras_leilao,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_vencedoras_leilao.columns = ['codigo','media_melhores','qtd_melhores','melhor']
df3_vencedoras_leilao['media_melhores'] = round(df3_vencedoras_leilao['media_melhores'],2)
df3_vencedoras_leilao['melhor'] = round(df3_vencedoras_leilao['melhor'],2)


####1.4.3 Op Perdedoras

op_perdedoras_leilao = df3_hora_leilao['liquido'] < 0
df3_perdedoras_leilao = df3_hora_leilao.loc[op_perdedoras_leilao,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_perdedoras_leilao.columns = ['codigo','media_piores','qtd_piores','pior']
df3_perdedoras_leilao['media_piores'] = round(df3_perdedoras_leilao['media_piores'],2)
df3_perdedoras_leilao['pior'] = round(df3_perdedoras_leilao['pior'],2)


####1.4.4 Valor por Ação

df3_valor_p_acao_leilao = df3_hora_leilao.loc[:,['codigo','valor_por_acao']].groupby('codigo').mean().reset_index().sort_values(by='valor_por_acao',ascending=False)
df3_valor_p_acao_leilao['valor_por_acao'] = df3_valor_p_acao_leilao['valor_por_acao']*100


####1.4.5 Tempo Operação

df3_tempo_p_op_leilao = df3_hora_leilao.loc[:,['codigo','duracao']].groupby('codigo').mean().reset_index().sort_values(by='duracao',ascending=False)
df3_tempo_p_op_leilao['duracao'] = round(df3_tempo_p_op_leilao['duracao'],2)


####1.4.6 Tabela Final

df3_combinado = pd.merge(df3_total_leilao,df3_vencedoras_leilao, on='codigo')
df3_combinado1 = pd.merge(df3_combinado, df3_perdedoras_leilao, on='codigo')
df3_combinado2 = pd.merge(df3_combinado1,df3_valor_p_acao_leilao, on='codigo')
df3_combinado_leilao = pd.merge(df3_combinado2,df3_tempo_p_op_leilao, on='codigo' )
nova_ordem_colunas = ['codigo','liquido','media_melhores','media_piores','melhor','pior','valor_por_acao','qtd_melhores','qtd_piores','duracao']
df3_combinado_leilao.reindex(columns=nova_ordem_colunas)
df3_combinado_leilao['% vencedoras'] = round(df3_combinado_leilao['qtd_melhores']/(df3_combinado_leilao['qtd_melhores'] + df3_combinado_leilao['qtd_piores']),2) 


#==========================###X Salada=================================================

hora_xsalada = df3_mes['hora'] > '17:00:00'
ativo_futuros = df3_mes['codigo'].str.startswith(('WDO','WIN','DOL','IND')) 
df3_xsalada = df3_mes.loc[hora_xsalada & ativo_futuros,:]
df3_xsalada = df3_xsalada.copy()
df3_xsalada.loc[:, 'codigo'] = df3_xsalada['codigo'].apply(lambda x: x[:3])



####1.5.1 Total Sala

df3_xsalada_total = df3_xsalada.loc[:,['liquido','codigo']].groupby('codigo').sum().reset_index()


####1.5.2 Op Vencedoras

op_vencedoras_xsalada = df3_xsalada['liquido'] > 0
df3_vencedoras_xsalada = df3_xsalada.loc[op_vencedoras_xsalada,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','max']}).reset_index()
df3_vencedoras_xsalada.columns = ['codigo','media_melhores','qtd_melhores','melhor']


####1.5.3 Op Perdedoras

op_perdedoras_xsalada = df3_xsalada['liquido'] < 0
df3_perdedoras_xsalada = df3_xsalada.loc[op_perdedoras_xsalada,['codigo','liquido']].groupby('codigo').agg({'liquido': ['mean','count','min']}).reset_index()
df3_perdedoras_xsalada.columns = ['codigo','media_piores','qtd_piores','pior']


####1.5.4 Valor Por Contrato

df3_valor_p_contrato_xsalada = df3_xsalada.loc[:,['codigo','valor_por_contrato']].groupby('codigo').mean().reset_index()


####1.5.5 Tempo Operação

df3_tempo_op_xsalada = df3_xsalada.loc[:,['codigo','duracao']].groupby('codigo').mean().reset_index()


####1.5.6 Tabela Final

df3_combinado = pd.merge(df3_xsalada_total,df3_vencedoras_xsalada, on='codigo')
df3_combinado1 = pd.merge(df3_combinado, df3_perdedoras_xsalada, on='codigo')
df3_combinado2 = pd.merge(df3_combinado1,df3_valor_p_contrato_xsalada, on='codigo')
df3_combinado_xsalada = pd.merge(df3_combinado2,df3_tempo_op_xsalada, on='codigo' )
nova_ordem_colunas = ['codigo','resultado','media_melhores','media_piores','melhor','pior','valor_por_contrato','qtd_melhores','qtd_piores','duracao']
df3_combinado_xsalada.reindex(columns=nova_ordem_colunas)
#Tabela Final
df3_combinado_xsalada['% vencedoras'] = round(df3_combinado_xsalada['qtd_melhores']/(df3_combinado_xsalada['qtd_melhores'] + df3_combinado_xsalada['qtd_piores']),2) 



#==============================================StreamLit=====================================================

with st.container():
    st.markdown("# Abertura Futuros")
    st.metric("Valor Total",value=round(df3_hora_abertura_futuros['liquido'].sum(),2))
    st.dataframe(df3_combinado_ab_futuros)
    st.markdown("""___""")
    
    st.markdown("# Futuros Tarde")
    st.metric("Valor Total",value=round(df3_futuros_tarde['liquido'].sum(),2))
    st.dataframe(df3_combinado_futuros_tarde)
    st.markdown("""___""")
    
    st.markdown("# Abertura Ações")
    st.metric("Valor Total",value=round(df3_abertura_acoes['liquido'].sum(),2))
    st.dataframe(df3_combinado_ab_acoes)
    st.markdown("""___""")
    
    st.markdown("# Leilão Fechamento")
    st.metric("Valor Total",value=round(df3_hora_leilao['liquido'].sum(),2))
    st.dataframe(df3_combinado_leilao)
    st.markdown("""___""")
    
    st.markdown("# X Salada")
    st.metric("Valor Total",value=round(df3_xsalada['liquido'].sum(),2))
    st.dataframe(df3_combinado_xsalada)
    st.markdown("""___""")