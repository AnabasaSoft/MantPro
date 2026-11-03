<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-6e7781?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-6e7781?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-0969da?style=for-the-badge" alt="Português"></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Fran%C3%A7ais-6e7781?style=for-the-badge" alt="Français"></a>
</p>

# MantPro

<p align="center">
  <img src="recursos/logo.png" alt="Logo do MantPro" width="200"/>
</p>

<p align="center">
  <strong>GMAO/CMMS gratuito e de código aberto para gerenciar a manutenção preventiva e corretiva da sua planta, oficina ou frota, pelo PC e pelo Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Auto--hospedado-gr%C3%A1tis%20para%20sempre-orange.svg" alt="Auto-hospedado: grátis para sempre">
</p>

---

## 📋 Índice

- [Que problema ele resolve?](#-que-problema-ele-resolve)
- [Para quem é?](#-para-quem-é)
- [Por que o MantPro?](#-por-que-o-mantpro-e-não-um-gmaocmms-comercial)
- [Vídeo de demonstração](#-vídeo-de-demonstração)
- [Capturas de tela](#-capturas-de-tela)
- [Downloads](#-downloads)
- [Recursos](#-recursos)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Usuários e acesso](#-usuários-e-acesso)
- [Máquinas](#-máquinas)
- [Estoque do almoxarifado](#-estoque-do-almoxarifado)
- [Sincronização PC-celular](#-sincronização-pc-celular)
- [Cópias de segurança](#-cópias-de-segurança)
- [Contribuir](#-contribuir)
- [Roteiro](#-roteiro)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🧩 Que problema ele resolve?

Em muitas oficinas e plantas pequenas e médias, a manutenção é controlada entre
papéis, uma planilha do Excel compartilhada e mensagens de WhatsApp. Funciona,
até que alguém precisa saber **o que foi feito em uma máquina específica**,
quem fez, quando e com qual material — e essa informação está espalhada em três
lugares diferentes (ou em nenhum).

**O MantPro centraliza isso**: cada técnico registra sua intervenção pelo
celular, na hora, com fotos de antes e depois se necessário, e tudo fica
organizado no PC por máquina, por data e por pessoa, pronto para consultar ou
gerar um relatório em PDF.

## 🎯 Para quem é?

Pensado para quem cuida da manutenção do dia a dia, não para departamentos de
TI: técnicos de manutenção, responsáveis de planta, oficinas, pequenas e médias
indústrias e encarregados de almoxarifado que precisam de um controle real de
máquinas, intervenções e estoque sem depender de planilhas soltas.

## 🆚 Por que o MantPro e não um GMAO/CMMS comercial?

- **Código aberto e grátis**: código aberto sob AGPL-3.0, sem limite de
  técnicos, máquinas ou registros
- **Auto-hospedado: grátis para sempre**: instalado no seu próprio PC ou servidor, não se paga por usuário nem por mês de uso
- **Seus dados, na sua infraestrutura**: o banco de dados fica no seu próprio
  PC; você não depende de que um serviço de nuvem de terceiros continue
  existindo no ano que vem
- **Offline de verdade**: o celular funciona sem conexão com a internet nem com
  o PC durante toda a jornada, e sincroniza assim que volta a ter rede
- **Feito a partir da própria manutenção**: as funções surgiram de
  necessidades reais de oficina (fotos de antes/depois, vínculo com a máquina,
  estoque de peças, avisos recorrentes...), não de uma lista genérica de
  requisitos de GMAO/CMMS

| | MantPro | GMAO/CMMS comercial típico |
|---|---|---|
| **Preço** | Grátis (auto-hospedado) | Mensalidade por usuário |
| **Usuários, máquinas e registros** | Sem limite | Conforme o plano contratado |
| **Onde ficam seus dados** | No seu PC ou servidor | Na nuvem do fornecedor |
| **App de celular sem conexão** | A jornada inteira | Muitas vezes limitado ou só consulta |
| **Almoxarifado de peças** | Incluído | Muitas vezes como módulo à parte |
| **Código-fonte** | Aberto (AGPL-3.0) | Fechado |
| **Se o fornecedor desaparecer** | Você continua usando | Você fica sem o serviço |

*Comparação com o modelo habitual dos GMAO/CMMS comerciais na nuvem; cada produto é diferente.*

## 🎬 Vídeo de demonstração

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Capturas de tela

### Aplicativo para desktop

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Painel" width="30%"/>
  <img src="Capturas/Maquinas.png" alt="Máquinas e peças de reposição" width="30%"/>
  <img src="Capturas/Almacen.png" alt="Gerenciamento do almoxarifado" width="30%"/>
</p>

### Aplicativo para celular

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Painel no celular" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Almoxarifado no celular" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Histórico no celular" width="30%"/>
</p>

---

## 📦 Downloads

Você pode baixar as versões pré-compiladas em [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: instalador (`MantPro_Setup_v….exe`) ou executável `.exe` avulso
- **Linux**:
  - Binário executável para Linux
  - AppImage portátil
  - Pacotes `.deb` (Debian, Ubuntu…) e `.rpm` (Fedora, openSUSE…), assinados com GPG
  - Também disponível no **AUR** (Arch User Repository)
  - Também disponível no [**OBS**](https://build.opensuse.org/package/show/home:danitxu79/MantPro) (openSUSE Build Service) para openSUSE Tumbleweed e Slowroll
- **Android**: arquivos `.apk` para instalação direta
  - `MantPro.apk`: aplicativo de serviços de manutenção
  - `MantProStock.apk`: aplicativo de estoque do almoxarifado

As versões marcadas como *pre-release* (`v3.10.2-dev`, `-rc.1`…) são de
teste: só são oferecidas como atualização a quem já tem uma versão de teste
instalada. Quem usa uma versão estável só recebe avisos de versões estáveis.
As mudanças de cada versão estão em [CHANGELOG.md](CHANGELOG.md).

---

## ✨ Recursos

### 💻 Aplicativo para desktop (PC)

- **👥 Gerenciamento de usuários**: login com usuário e senha, funções de administrador e técnico, cadastro e desativação de usuários e redefinição de senhas
- **✍️ Autoria dos serviços**: cada intervenção guarda quem a realizou, visível no histórico e nos relatórios
- **🔒 Permissões por registro**: um técnico só pode editar ou excluir seus próprios serviços; um administrador pode gerenciar qualquer um, inclusive reatribuir o autor de um ou vários registros de uma vez
- **📋 Registro de Alterações**: quem alterou o quê, quando e de onde (PC ou celular) em serviços, pendentes, avisos, checklists, máquinas, almoxarifado, usuários, segurança e configurações, com cada campo antes → depois; filtros, busca e exportação para Excel/CSV (somente administradores)
- **🔐 Sessões de dispositivos**: lista os celulares vinculados a cada usuário, com o modelo real, e permite revogar uma ou várias sessões específicas sem desativar o usuário inteiro (somente administradores). Ao entrar de novo pelo mesmo dispositivo, a sessão anterior é substituída automaticamente em vez de se acumular
- **🛡️ Segurança**: sincronização com os celulares criptografada por HTTPS (o certificado do PC fica fixado pelo QR), **bancos de dados criptografados** opcionais (SQLCipher, com a chave no chaveiro do sistema) e **cópias de segurança criptografadas com senha**, tentativas de login limitadas contra força bruta, fotos recebidas dos celulares verificadas e cópias consistentes com verificação de integridade
- **📊 Painel com KPIs e gráficos**: cartões de avisos pendentes, tarefas a fazer, registros do mês e MTBF/MTTR médios de toda a planta, além de gráficos das máquinas com mais falhas e de falhas por mês, desenhados sem depender de bibliotecas externas
- **🎨 Temas visuais**: escolha entre modo escuro (padrão), claro ou um estilo retrô inspirado no Windows 98, no menu "Aparência"
- **📅 Calendário interativo**: visualize e gerencie as tarefas de manutenção com códigos de cores (feriados, férias, dias com tarefas)
- **📝 Histórico completo**: registro histórico de todas as intervenções realizadas, com fotos de antes/depois e uma **coleção de fotos** adicional por serviço; é possível excluir vários registros de uma vez
- **📄 Relatórios em PDF**: geração automática de relatórios profissionais com logo personalizável
- **📸 Gerenciamento de imagens**: armazenamento e visualização das fotos das intervenções
- **📱 Sincronização com o celular**: servidor integrado (inicia automaticamente) para sincronizar com o aplicativo do celular via QR
- **🔍 Sistema de busca**: busca avançada por datas, tags e conteúdo
- **👤 Filtro por técnico**: filtre o histórico e as exportações (PDF, CSV e Excel) pela pessoa que fez o serviço
- **📦 Backup e restauração**: cópia manual completa (BD + fotos) escolhendo onde salvá-la, backup automático incremental ao fechar o aplicativo (veja [Cópias de segurança](#-cópias-de-segurança)) e restauração com barra de progresso, com o submenu `Arquivo > ♻️ Restaurar` para escolher entre qualquer backup manual ou ir direto às cópias automáticas. As cópias podem ser **criptografadas com senha** (`Arquivo > 🔒 Senha das cópias…`)
- **🏷️ Sistema de tags**: classificação com etiquetas (Urgente, Elétrico, Mecânico, Preventivo)
- **🔨 Tarefas pendentes**: gerenciamento de serviços pendentes (criar, concluir, editar, excluir) e **atribuição a um técnico específico**
- **🚦 Prioridade dos pendentes**: cada serviço pendente tem uma prioridade (Baixa, Média, Alta ou Crítica) para decidir qual atacar primeiro, com sua cor na lista; também é possível anexar fotos à coleção dele
- **↩️ Reverter para pendente**: se um serviço foi concluído por engano, ele pode voltar para Pendentes com um clique a partir do histórico (com aviso se tinha máquina vinculada, já que esse dado se perderia), ficando registrado na auditoria
- **🔁 Lembretes**: avisos de manutenção que se repetem automaticamente. Se a data passar, eles não são pulados: ficam **Pendentes** (laranja) durante a margem e depois **Atrasados** (vermelho) até serem feitos, e a próxima data é contada a partir do dia em que o serviço foi realmente feito
- **📟 Preventiva por contador**: avisos por **horas de uso, ciclos ou km** de uma máquina («troca de óleo a cada 500 h, avisar 50 h antes»), sozinhos ou junto com uma frequência por data (**o que vier primeiro**: «a cada 500 h ou a cada ano»). As leituras são anotadas no PC, na ficha da máquina no celular (também sem conexão) e ao concluir a preventiva; o próximo conta a partir dessa leitura, e estima-se quando será atingido pelo uso médio
- **☑️ Checklists**: modelos reutilizáveis («Revisão mensal do compressor») com itens marcados como OK / com problema / não se aplica e leituras com a unidade e a faixa correta (fora da faixa, «com problema» automaticamente); são atribuídos a avisos e serviços pendentes e preenchidos ao concluí-los, no PC ou no celular (também sem conexão). Ficam salvos com o serviço, aparecem no histórico e nas exportações em PDF, Excel e CSV
- **📦 Controle do estoque do almoxarifado**: estrutura configurável de estantes, prateleiras e seções, ficha de materiais com foto, entradas/saídas com histórico e alertas de estoque abaixo do mínimo
- **📄 Exportar o estoque**: botão "📄 Exportar" na aba de estoque para gerar o almoxarifado inteiro, uma zona ou uma estante em PDF, CSV ou Excel, ordenado por localização; a aba de estoque abaixo do mínimo também tem seu botão para exportar apenas os materiais em alerta
- **🗑️ Tempo máximo de armazenamento**: `Ferramentas` permite excluir do histórico os serviços mais antigos que um número de anos, meses ou dias, com suas fotos e uma cópia de segurança prévia (somente administradores)
- **📥 Importar do Excel/CSV**: `Arquivo > Importar do Excel/CSV…` (somente administradores) traz máquinas, itens do almoxarifado, avisos recorrentes e usuários de um modelo para baixar ou do seu próprio Excel (uma planilha ou a pasta de trabalho inteira de uma vez), associando as colunas automaticamente, com pré-visualização linha a linha e cópia de segurança prévia. Localizações (zonas, estantes, prateleiras) e máquinas superiores que não existirem são criadas automaticamente, e os usuários recebem uma senha temporária que terão de alterar no primeiro acesso
- **🏭 Controle de máquinas**: árvore de máquinas e submáquinas com foto anexada, contador de serviços por ano e mês e vínculo direto a partir de cada serviço registrado ou editado (veja [Máquinas](#-máquinas))
- **📊 Exportação**: para PDF, CSV e Excel, com filtro opcional por técnico e indicando a máquina/submáquina de cada serviço, se houver
- **📖 Ajuda integrada**: `Ajuda > 📖 Instruções` abre um manual completo por tópicos (primeiros passos, usuários, cada aba, menus, aplicativos do celular e problemas comuns), com índice e busca, nos 7 idiomas. Com **F1** ele abre direto no tópico da aba em que você está
- **👥 Estatísticas por técnico**: botão no Painel com os serviços de cada técnico por ano e mês, falhas, preventivos, horas de parada e pendentes atribuídos agora, com gráfico de barras; filtrável por tipo (todos, serviços e falhas ou manutenção preventiva) e exportável para PDF (com logo) e Excel
- **🔩 Peças de reposição por máquina**: quais itens do almoxarifado cada máquina leva e quantos, com seu estoque e localização, e em quais máquinas cada item é usado (veja [Máquinas](#-máquinas))
- **💶 Peças usadas e seu custo**: ao registrar, concluir ou editar um serviço, anotam-se as peças usadas (as da máquina aparecem primeiro); elas saem do estoque e ficam salvas com o serviço e o preço daquele momento, então o custo não muda mesmo que o preço mude depois. Ao corrigi-las, o estoque é ajustado. Cada item pode ter preço unitário (moeda configurável). `Máquinas > 💶 Custo de peças` mostra o custo por máquina, incluindo as submáquinas, por ano e exportável para Excel; o histórico, o PDF, o Excel e o CSV as incluem
- **⏱️ Tempo trabalhado**: quanto durou cada serviço e quantas pessoas, **anotado depois** (sem cronômetro: numa avaria primeiro se conserta), no PC ou no celular, também ao concluir avisos e pendentes, e corrigível no histórico. Com um custo da hora interno (somente administradores; cada serviço guarda a tarifa do momento), `Máquinas > 💶 Custos` mostra horas, mão de obra, peças e total por máquina, e as estatísticas por técnico incluem suas horas
- **🏷️ Etiquetas QR por máquina**: PDF de etiquetas para colar nas máquinas; ao escaneá-las com o aplicativo MantPro abre-se a ficha da máquina
- **🔍 Aviso de duplicados**: ao criar ou renomear uma máquina, ou ao criar ou editar um item, avisa se já existe outro com o mesmo código ou um nome igual ou muito parecido (por exemplo «Extrator de finos» / «Extração de finos»), sem avisar quando só muda o número («Lora 1» / «Lora 2»)
- **📲 Instalar os aplicativos com um QR**: `Ferramentas > 📱 Instalar MantPro no celular` e `📦 Instalar MantPro Stock no celular` mostram um QR que, ao ser escaneado com a câmera do celular, baixa a última versão estável do aplicativo
- **🔔 Avisos de atualização**: `Ajuda > 🔄 Procurar Atualizações` avisa das novas versões; a instalada pelo OBS (openSUSE) indica que é atualizada com `zypper`

### 📱 Aplicativo para celular (Android)

- **🔐 Acesso com usuário**: cada técnico entra uma vez e a sessão fica salva no dispositivo (o token fica guardado no Keystore do Android, não em texto puro)
- **📝 Registro rápido**: registro de intervenções em campo, assinadas automaticamente com o seu usuário
- **📷 Câmera integrada**: tire fotos e edite-as com anotações
- **🖼️ Coleção de fotos**: além das fotos de antes e depois, adicione a um serviço ou pendente quantas fotos quiser (câmera ou galeria); ao tocar em qualquer foto, ela é exibida em tela cheia, passando de uma para outra e ampliando com dois dedos
- **✏️ Editor de imagens**: desenhe sobre as fotos para marcar áreas de interesse
- **🔄 Sincronização automática**: envio automático dos dados para o PC via código QR
- **💾 Armazenamento local**: guarda os registros offline até sincronizar
- **📋 Serviços pendentes**: visualize e gerencie as tarefas atribuídas pelo PC, com o filtro **"Só os meus"**
- **🔄 Atualização ao abrir**: ao iniciar, o aplicativo sincroniza em segundo plano os dados de todas as abas
- **🔁 Sincronizar manualmente**: as abas Pendentes, Histórico e Lembretes têm seu próprio botão para reenviar na hora o que o celular tiver e o PC ainda não
- **↩️ Reverter para pendente**: mantendo pressionado um registro do Histórico, ele pode voltar para a aba Pendentes se foi concluído por engano
- **🏷️ Tags rápidas**: sistema de etiquetas rápido com caixas de seleção
- **☑️ Checklists**: os avisos e serviços pendentes com checklist pedem para preenchê-lo ao concluí-los (OK / com problema / não se aplica e leituras), também sem conexão; o histórico mostra o checklist preenchido
- **🔌 Modo offline**: trabalhe sem conexão e sincronize quando puder
- **⏰ Lembretes diários**: notificação automática às 8:00 (horário local) se houver serviços pendentes não concluídos
- **🧰 Material usado**: adicione ao serviço o material do almoxarifado que você usou, buscando pelo nome ou código; ele é descontado do estoque automaticamente ao salvar (veja [Material usado em um serviço](#-estoque-do-almoxarifado)). Ao concluir um aviso também é possível anotar peças, as da máquina aparecem primeiro, e ao corrigir um serviço do histórico o estoque é ajustado
- **🏭 Vincular máquina**: escolha em uma lista a máquina ou submáquina em que o serviço foi feito, tanto ao criar um registro novo quanto ao editar um já sincronizado do histórico
- **🔄 Conectado em segundo plano**: enquanto o aplicativo está aberto, mesmo em segundo plano, ele continua sincronizando com o PC e mostra uma notificação («Conectado ao PC» / «Sem conexão com o PC») com um botão «Fechar». Ao fechá-lo totalmente, ele para de gastar bateria
- **📶 Primeira sincronização com progresso**: barra de progresso ao baixar os dados e as fotos, com download em paralelo para ser mais rápido
- **🏷️ Escanear a máquina**: o botão de escanear lê a etiqueta QR de uma máquina e abre sua ficha, sem conexão: onde ela está, seus últimos serviços, suas **peças de reposição** com o estoque do almoxarifado, e um botão para registrar um serviço já vinculado a ela
- **📟 Contadores da máquina**: na ficha da máquina anotam-se as leituras dos contadores (horas, ciclos, km) sem conexão e veem-se as preventivas por contador com o que falta; ao concluir uma, a leitura é anotada no mesmo passo
- **⬆️ Atualizar pelo aplicativo**: quando há uma versão nova, o aviso tem os botões «Depois» e «Atualizar»; «Atualizar» baixa o APK com uma barra de progresso e abre o instalador do Android, sem passar pelo GitHub

### 📦 Aplicativo de estoque para celular (Android)

Aplicativo independente (`mantpro_stock_app`), pensado para consultar e
movimentar o estoque do almoxarifado pelo celular sem precisar do aplicativo de
serviços.

- **🔐 Acesso com usuário**: usa o mesmo sistema de usuários e sessão do aplicativo de serviços (o token fica guardado no Keystore do Android, não em texto puro)
- **🗂️ Navegação pelo almoxarifado**: árvore de estantes > prateleiras > seções, igual ao PC
- **🔎 Busca de materiais**: por nome, código, descrição ou localização
- **➕➖ Entradas e saídas**: registre movimentações de estoque pelo celular, com motivo opcional
- **🔀 Transferências**: mover um material de seção fica registrado no histórico de movimentações dele
- **🎨 Aviso visual de estoque**: quantidade em vermelho abaixo do mínimo, em verde acima e na cor padrão se for exatamente igual
- **⚠️ Estoque abaixo do mínimo**: aba dedicada aos materiais em alerta
- **🔄 Atualização automática**: a tela se atualiza sozinha ao detectar alterações, feitas tanto no próprio celular quanto no PC
- **🔌 Modo offline**: sem conexão com o PC, o aplicativo não fica esperando: consulta os dados salvos e permite registrar cadastros, edições, entradas e saídas na hora, que são enviados sozinhos ao PC assim que ele voltar a estar acessível
- **🔔 Lembrete diário de conferência de estoque**: notificação automática às 8:00 (horário local) convidando a conferir a quantidade real de 5 materiais do almoxarifado, escolhidos ao acaso e diferentes a cada dia; ao tocá-la, abre-se uma tela para corrigir a quantidade de cada um sem precisar procurá-los. Se não houver nenhum material cadastrado, nenhuma notificação é exibida
- **🔄 Conectado em segundo plano**: como o MantPro, continua sincronizando em segundo plano, com sua notificação; o ícone de usuário fica **verde** se há conexão com o PC e **vermelho** se não há
- **🔩 Usado em**: cada item mostra em quais máquinas é usado como peça de reposição e quantos cada uma leva, também sem conexão
- **🔍 Aviso de duplicados**: ao criar ou editar um item, avisa se já existe outro com o mesmo código ou um nome muito parecido, comparando com os itens salvos no celular (funciona sem conexão)
- **⬆️ Atualizar pelo aplicativo**: como o MantPro, baixa e instala a nova versão a partir do próprio aviso

---

## 🔧 Requisitos

### Aplicativo para desktop

- **Python**: 3.10 ou superior
- **Sistema operacional**: Windows ou Linux
- **Dependências do Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - Pillow
  - cryptography
  - keyring e sqlcipher3-wheels (opcionais: criptografia dos bancos de dados)
  - sqlite3 (incluído no Python)

### Aplicativo para celular

Vale tanto para o `mantenimiento_app` (serviços) quanto para o `mantpro_stock_app` (estoque):

- **Flutter**: 3.0 ou superior
- **Dart SDK**: 2.17 ou superior
- **Android**: API Level 24+ (Android 7.0+)

---

## 📥 Instalação

### Aplicativo para desktop

#### Opção 1: download pré-compilado (recomendado)

Baixe a versão correspondente ao seu sistema em [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: baixe e execute o `.exe`
- **Linux**:
  - Baixe o binário executável e dê permissão de execução: `chmod +x mantpro`
  - Ou use o **AppImage** (sem instalação): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - Os pacotes **`.deb`** e **`.rpm`** são assinados digitalmente com GPG (veja [Verificar a assinatura dos pacotes](#-verificar-a-assinatura-dos-pacotes-linux))
  - **Arch Linux**: disponível no AUR: `yay -S mantpro` ou `paru -S mantpro`
  - **openSUSE Tumbleweed / Slowroll**: disponível no [OBS](https://build.opensuse.org/package/show/home:danitxu79/MantPro), compilado com o Python e o PyQt6 da própria distribuição e atualizado com `zypper`:
    ```bash
    sudo zypper ar -f https://download.opensuse.org/repositories/home:/danitxu79/openSUSE_Tumbleweed/home:danitxu79.repo
    sudo zypper in mantpro
    ```
    (no Slowroll, troque `openSUSE_Tumbleweed` por `openSUSE_Slowroll` na URL)

#### 🔏 Verificar a assinatura dos pacotes (Linux)

Os pacotes `.deb` e `.rpm` publicados em cada release são assinados com a chave GPG oficial da AnabasaSoft. Para verificá-los antes de instalar:

**Impressão digital da chave** (confira também em [anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma)): `11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199` (RSA 4096, expira em 2028-10-06). Se a que o `gpg` mostrar não coincidir exatamente, não instale o pacote.

1. Baixe a chave pública do repositório ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) para um arquivo (**não use `curl | rpm --import -`**: algumas versões do `rpm` não aceitam ler a chave pela entrada padrão e falham):
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Importe a chave (só é preciso uma vez por computador):
   ```bash
   # Fedora, openSUSE, RHEL... (pacote .rpm)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (pacote .deb, requer dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Verifique se a chave foi importada corretamente:
   ```bash
   # RPM
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft

   # DEB (ou qualquer distribuição com gpg): mostra também a impressão digital
   gpg --fingerprint AnabasaSoft
   ```

4. Verifique a assinatura do pacote baixado:
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   Uma assinatura correta mostra `OK` na linha da assinatura (em vez de `NOKEY` ou `MISSING KEYS`).

Uma assinatura válida confirma que o pacote vem da AnabasaSoft e que não foi modificado.

#### Opção 2: instalação a partir do código-fonte

1. **Clonar o repositório**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Criar um ambiente virtual** (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instalar as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar o aplicativo**:
   ```bash
   python main.py
   ```

### Aplicativo para celular

#### Opção 1: download direto (recomendado)

Baixe o `.apk` correspondente em [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) e instale-o no seu dispositivo Android: `MantPro.apk` para os serviços, `MantProStock.apk` para o estoque do almoxarifado. São aplicativos independentes e você pode instalar um, o outro ou os dois.

**Observação**: talvez seja necessário habilitar "Fontes desconhecidas" nas configurações de segurança do dispositivo.

**Pelo PC, com um QR**: em `Ferramentas > 📱 Instalar MantPro no celular` (ou
`📦 Instalar MantPro Stock no celular`) aparece um QR. Escaneie-o com a câmera
do celular, abra o link e a última versão estável do aplicativo é baixada.
Depois de instalados, os aplicativos avisam das novas versões e se atualizam a
partir do próprio aviso com o botão «Atualizar».

#### Opção 2: compilar a partir do código-fonte

1. **Entrar no diretório do aplicativo** (`mantenimiento_app` para os serviços, `mantpro_stock_app` para o estoque):
   ```bash
   cd mantenimiento_app
   ```

2. **Instalar as dependências**:
   ```bash
   flutter pub get
   ```

3. **Executar em um dispositivo ou emulador**:
   ```bash
   flutter run
   ```

4. **Compilar o APK (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Uso

### Primeira configuração

#### Aplicativo para desktop

1. **Iniciar o aplicativo**: execute `python main.py` (o servidor de sincronização inicia sozinho, não é preciso iniciá-lo manualmente)
2. **Primeiro acesso**: na primeira execução é criado o usuário `admin` com a senha `admin`. O aplicativo **obriga a alterá-la** ao entrar
3. **Criar os usuários**: menu `Ferramentas` > `👥 Gerenciamento de usuários` > cadastre cada técnico
4. **Configurar o logo** (opcional): menu `Arquivo` > `📤 Exportar` > `📄 Opções de PDF` > `🖼️ Adicionar / Alterar Logo`
5. **Registrar um serviço**: aba "📝 Registrar" > preencha o resumo e os detalhes > "💾 SALVAR REGISTRO"
6. **Criar um pendente**: aba "🔨 Pendentes" > grupo "Novo Serviço" (Título + Detalhes + "Atribuir a") > "Adicionar"

#### Aplicativo para celular

1. **Instalar o aplicativo** no seu celular
2. **Conectar ao PC**:
   - Verifique se o PC e o celular estão na mesma rede Wi-Fi
   - No PC: menu `Ferramentas` > `📲 Sincronizar App (QR)`
   - No celular: toque em "Vincular PC" e escaneie o código
3. **Entrar**: informe o usuário e a senha que o administrador criou para você. A sessão fica salva: só é preciso fazer isso uma vez
4. **Pronto**: você já pode registrar intervenções pelo celular

### Fluxo de trabalho típico

#### Pelo PC

1. **Criar e atribuir uma tarefa pendente**:
   - Aba "🔨 Pendentes" > grupo "Novo Serviço" > preencha o Título e os Detalhes, escolha o técnico em "Atribuir a" > "Adicionar"
   - Gerencie-a com os botões "✅ Concluir", "✏️ Editar", "❌ Excluir" ou "👤 Reatribuir"
   - A lista "Ver os de" filtra por técnico (inclui "Sem atribuição")

2. **Revisar os serviços concluídos**:
   - Os serviços sincronizados pelo celular aparecem automaticamente
   - Confira as fotos (antes/depois e coleção) e os detalhes na aba "📋 Histórico" ou no "📅 Calendário"
   - A coluna "Realizado por" indica quem fez cada serviço, e a lista acima permite ver apenas os de uma pessoa

3. **Gerar relatórios**:
   - Menu `Arquivo` > `📤 Exportar` > `📄 Opções de PDF` > `📄 Gerar PDF Agora`
   - Na janela você pode escolher o técnico, e o nome dele aparece no título do relatório
   - Ou exporte para `📄 CSV` / `📊 Excel` em `Arquivo` > `📤 Exportar`

#### Pelo celular

1. **Vincular ao PC e entrar** (só na primeira vez, ou se mudar de rede):
   - Toque em "Vincular PC" e escaneie o QR exibido pelo PC
   - Informe seu usuário e senha
   - O celular guarda o endereço do PC e a sua sessão para sincronizar automaticamente a partir daí

2. **Registrar uma intervenção**:
   - Toque em "Novo" ou selecione um serviço pendente já sincronizado pelo PC
   - Com o filtro "Só os meus" você vê apenas os serviços atribuídos a você
   - Preencha o título e os detalhes
   - Tire a foto de "antes" e, se quiser, a de "depois" com a câmera; se precisar, adicione mais à coleção de fotos
   - Desenhe ou faça anotações na foto, se necessário
   - Selecione as tags adequadas
   - Salve

3. **Sincronizar**:
   - Ao abrir o aplicativo, tudo é sincronizado em segundo plano (você verá um indicador na barra superior)
   - Você também pode forçar a sincronização puxando a lista para baixo ou com o ícone de sincronização
   - Os registros são enviados ao PC e removidos do celular quando o envio é confirmado
   - Tudo funciona sem conexão: o que estiver pendente fica salvo e é enviado quando houver sinal

---

## 👥 Usuários e acesso

### Funções

Um mesmo usuário pode ter **uma ou várias funções ao mesmo tempo** (por
exemplo, técnico e almoxarifado). Funções disponíveis:

| Função | O que pode fazer |
|--------|------------------|
| **Administrador** | Tudo o que o técnico e o almoxarifado fazem, além de cadastrar e desativar usuários, alterar funções, redefinir senhas, editar ou excluir **qualquer** registro do histórico, reatribuir o autor de um ou vários registros de uma vez e consultar o registro de auditoria de alterações |
| **Técnico** | Registrar serviços, concluir pendentes e avisos, editar ou excluir **apenas os próprios** registros do histórico e alterar a própria senha |
| **Almoxarifado** | Cadastrar ou editar materiais e registrar entradas/saídas de estoque pelo aplicativo **MantPro Stock** |

Sempre deve existir **pelo menos um administrador ativo**: o aplicativo impede
remover a função ou desativar o último que restar.

> No aplicativo para desktop, qualquer usuário (seja qual for sua função) pode
> registrar movimentações de estoque; a função **Almoxarifado** é o que habilita
> esse mesmo gerenciamento (cadastros, edições e movimentações) pelo celular.

### Gerenciamento pelo PC

- **Cadastro**: `Ferramentas` > `👥 Gerenciamento de usuários` > preencha
  usuário, nome, senha e função > "➕ Adicionar". Se você deixar marcado "Pedir
  alteração ao entrar", a pessoa terá de definir a própria senha no primeiro
  acesso.
- **Desativação**: é feita de forma **lógica** (o usuário fica inativo). Ele
  nunca é apagado, para não quebrar a autoria dos serviços que já fez.
- **Redefinir senha**: útil quando alguém a esquece. Ao alterá-la, todas as
  sessões abertas dessa pessoa no celular são encerradas automaticamente.
- **Alterar a própria senha**: `Ferramentas` > `🔑 Alterar minha senha`.

### Sessões de dispositivos

`Ferramentas` > `🔐 Sessões de dispositivos` (somente administradores) lista
todas as sessões abertas no celular de todos os usuários, com o modelo do
dispositivo, quando começou, quando expira e se continua ativa ou já expirou.
É possível selecionar uma ou várias linhas e revogá-las, o que encerra a sessão
daquele celular sem precisar desativar o usuário inteiro (o que encerraria
*todos* os dispositivos dele de uma vez).

Se um usuário entrar de novo por um dispositivo em que já tinha uma sessão
aberta (mesmo fabricante e modelo), a sessão anterior desse dispositivo é
apagada automaticamente ao criar a nova, em vez de ficar acumulada como mais
uma sessão solta na lista.

As sessões expiram por inatividade: cada vez que o telemóvel liga ao PC a sua
sessão é renovada, pelo que quem usa a app não tem de voltar a iniciar sessão,
e fecham-se sozinhas após **60 dias sem ligar** (um telemóvel perdido ou de
alguém que já não está). O administrador altera esse prazo (de 30 a 365 dias)
na mesma janela. O que o telemóvel tivesse por enviar não se perde: é enviado
ao voltar a iniciar sessão.

A coluna **Conexão** indica se cada celular está **online** agora e quando foi
seu último contato. Os aplicativos avisam o PC a cada poucos segundos enquanto
estão abertos (também em segundo plano), e ao serem fechados totalmente avisam
que estão se desconectando, então o estado é atualizado na hora.

### Autoria dos serviços

Cada registro guarda o técnico que o fez, tenha sido criado no PC ou vindo do
celular. Os registros anteriores à implantação do sistema de usuários ficaram
marcados como **`Histórico`**.

No celular, a atribuição é decidida **sempre pelo servidor** a partir do token
da sessão, nunca por um dado enviado pelo aplicativo. Um dispositivo não pode
assinar serviços em nome de outra pessoa.

Pelo PC, um técnico só pode editar ou excluir os próprios registros do
histórico; um administrador pode fazer isso com qualquer um. Clicando com o
botão direito sobre uma ou várias linhas do histórico (seleção múltipla com
Ctrl/Shift), um administrador também pode **reatribuir o autor** em bloco, e
cada alteração fica anotada no registro de auditoria.

### Registro de alterações (auditoria)

Os administradores veem em `Ferramentas` > `📋 Registro de alterações` **quem
alterou o quê, quando e de onde** (o PC ou qual celular): serviços, serviços
pendentes, avisos, checklists, máquinas e peças de reposição, itens e estrutura
do almoxarifado, usuários e especialidades, segurança (sessões revogadas,
bloqueios por tentativas erradas, criptografia, conexão sem criptografia),
cópias restauradas, importações e configurações. Cada alteração mostra os
campos afetados **antes → depois**. É possível filtrar por categoria, ação,
usuário e período, buscar por texto e exportar para Excel ou CSV.

### Sessão no celular

O técnico entra uma vez e o token fica salvo no dispositivo. A sessão é
encerrada sozinha se o administrador desativar o usuário ou redefinir a senha
dele; nesse caso, o aplicativo volta para a tela de acesso **sem perder os
registros que ainda estiverem pendentes de envio**.

O token de sessão fica guardado no **Keystore do Android** (armazenamento seguro), não em texto puro. Depois de **5 tentativas de login erradas** seguidas, esse usuário fica bloqueado por 15 minutos (e um celular, depois de 20 tentativas erradas); o aplicativo mostra quanto tempo falta. Na janela do PC, 5 erros bloqueiam o login por um minuto.

---

## 🏭 Máquinas

> Gerenciamento disponível no aplicativo para desktop, com o vínculo à máquina
> também selecionável pelo celular ao registrar ou editar um serviço.

Aba "🏭 Máquinas" do PC, pensada para acompanhar as falhas e intervenções de
cada equipamento ao longo do tempo.

- **🌳 Árvore de máquinas**: as máquinas podem ter submáquinas (por exemplo,
  uma linha com vários equipamentos), formando uma hierarquia tão profunda
  quanto necessário
- **📅 Serviços organizados por ano e mês**: ao expandir uma máquina aparecem
  os anos com serviços e, ao expandir um ano, os meses; cada nível mostra um
  contador de quantos serviços tem, com carregamento sob demanda para não
  deixar a árvore lenta
- **🖱️ Acesso direto ao serviço**: com um clique duplo sobre um serviço da
  árvore, abre-se diretamente a ficha de edição dele
- **📸 Foto da máquina**: cada máquina ou submáquina pode ter uma foto anexada,
  visível em um quadro ao lado da árvore ao selecioná-la
- **🔗 Vínculo a partir de cada serviço**: ao registrar um serviço novo (PC ou
  celular) ou editar um existente, é possível escolher a qual
  máquina/submáquina ele pertence
- **📊 Nas exportações**: a máquina ou submáquina vinculada aparece como coluna
  adicional nas exportações para PDF, CSV e Excel
- **🗺️ Zona herdada**: ao criar uma submáquina, ela recebe por padrão a zona
  da sua máquina superior
- **🔩 Peças de reposição de cada máquina**: abaixo da árvore aparecem os itens
  do almoxarifado montados na máquina selecionada, quantos ela leva, seu
  estoque (em vermelho se abaixo do mínimo), sua localização e uma observação
  (por exemplo «lado do motor»). São adicionados com «➕ Adicionar peça»,
  exportados para PDF ou Excel, e com clique duplo você vai ao item no
  almoxarifado
- **🏷️ Etiquetas QR**: o botão «🏷️ Etiquetas QR» gera um PDF de folhas A4 com
  24 etiquetas de 70 × 37 mm (da máquina selecionada, com suas submáquinas ou
  de todas). Ao escaneá-las com o aplicativo MantPro abre-se a ficha da
  máquina
- **📟 Contadores**: o botão «📟 Contadores» gerencia as horas de uso, ciclos
  ou km da máquina selecionada (criados por um administrador), com a última
  leitura, o uso médio por dia e o histórico de leituras. As preventivas por
  contador usam essas leituras
- **🔍 Nomes parecidos**: ao criar ou renomear uma máquina, avisa se no mesmo
  nível já existe outra com um nome igual ou muito parecido

---

## 📦 Estoque do almoxarifado

> Gerenciamento completo pelo aplicativo para desktop, com consulta e
> movimentações também disponíveis pelo celular (`mantpro_stock_app`). Fica
> em um banco de dados próprio (`almacen.db`), independente do dos serviços de
> manutenção.

### Estrutura do almoxarifado

O almoxarifado é organizado em três níveis, inspirados nas convenções
habituais de endereçamento de almoxarifados:

```
Estante → Prateleira → Seção
```

- Ao criar uma estante, define-se o **número de prateleiras**, o **número de
  seções por prateleira** (0 = sem seções predefinidas, que podem ser
  adicionadas depois) e se ela tem **espaço no chão** abaixo da prateleira
  inferior, tratado como uma prateleira especial ("Chão")
- As prateleiras são numeradas de baixo para cima a partir de 1, para poder
  adicionar prateleiras novas sem renumerar as existentes
- Não é possível excluir uma estante, prateleira ou seção enquanto houver
  material guardado nela

A estrutura é gerenciada pelo botão **"⚙️ Configurar almoxarifado"** da aba
"📦 Estoque do almoxarifado", visível **somente para administradores**.

### Materiais

- Cadastro e edição com código (opcional), nome, descrição, unidade, estoque
  mínimo, localização (estante / prateleira / seção) e **foto anexada**
- Busca por **nome, código, descrição ou localização**
- O estoque é destacado em **vermelho** abaixo do mínimo, em **verde** acima e
  na cor padrão se for exatamente igual ao mínimo, tanto no PC quanto no
  celular
- Selecionando vários materiais de uma vez (Ctrl/Shift + botão direito) no PC,
  é possível **mudá-los de localização** ou **excluí-los** em bloco
- Cada item indica **em quais máquinas é usado** como peça de reposição, e ao
  criá-lo ou editá-lo é possível associar máquinas diretamente, com a
  quantidade que cada uma leva
- Ao criar ou editar um item, avisa-se se já existe outro com o **mesmo código
  ou um nome muito parecido**, para não cadastrá-lo duas vezes

### Entradas, saídas e transferências

- **Qualquer usuário** pode registrar entradas e saídas de estoque; somente a
  configuração da estrutura do almoxarifado é restrita a administradores
- Cada movimentação fica registrada com data, quantidade, usuário e um motivo
  opcional, visível no histórico de cada material
- As saídas registradas manualmente (PC ou `mantpro_stock_app`) não podem
  deixar o estoque negativo
- Mudar um material de localização também fica registrado no histórico dele,
  como uma movimentação do tipo **transferência** (de qual seção para qual
  seção)
- O botão **«📜 Histórico»** mostra todas as movimentações do almoxarifado em
  sequência (entradas, saídas e transferências), com o nome de cada item e
  filtros por texto e tipo

### Material usado em um serviço (MantPro)

Ao concluir um serviço pelo aplicativo **MantPro** (celular), é possível
adicionar o material usado, buscando-o pelo nome ou código e informando a
quantidade. Ao salvar o serviço, esse material é descontado automaticamente do
almoxarifado, com o motivo "Usado em serviço: ..." para manter a
rastreabilidade.

Ao contrário das saídas manuais, **esse desconto pode deixar o estoque
negativo**: o material já foi usado fisicamente no serviço, mesmo que não
houvesse estoque registrado suficiente, então bloquear a movimentação não
faria sentido. O estoque negativo aparece tanto no PC quanto no
`mantpro_stock_app` e serve de aviso de que é preciso conferir e repor esse
material o quanto antes.

### Alertas de estoque abaixo do mínimo

A aba **"⚠️ Estoque abaixo do mínimo"** mostra, em uma visualização separada,
os materiais sem estoque ou abaixo do mínimo definido. O próprio título da aba
indica quantos materiais estão em alerta, e dali é possível ir direto ao
material em "Estoque do almoxarifado", registrar uma entrada sem trocar de aba
ou exportar a lista com o botão "📄 Exportar".

### Exportar o estoque

Na aba **"📦 Estoque do almoxarifado"** do PC, o botão **"📄 Exportar"** abre
uma janela para escolher o **formato** (PDF, CSV ou Excel) e **o que
exportar**: o almoxarifado inteiro, uma zona ou uma só estante. A lista sai
ordenada por localização, para percorrer o almoxarifado com ela em mãos; o PDF
e o Excel incluem ainda a data, o número de materiais e quantos estão abaixo
do mínimo (em vermelho). A própria tabela de estoque também é exibida ordenada
por localização por padrão (Estante 1, 2… 10).

---

## 🔄 Sincronização PC-celular

### Como funciona

O MantPro usa um sistema de sincronização baseado em:

1. **Servidor Flask** integrado ao aplicativo para desktop
2. **Códigos QR** para uma conexão rápida e segura
3. **API REST autenticada por token**: todos os endpoints de dados exigem uma
   sessão válida; se o token deixar de valer, o servidor responde `401` e o
   celular volta para a tela de login
4. **Wi-Fi local**, sem precisar de internet
5. **Sincronização completa ao abrir o aplicativo**, em segundo plano e sem
   travar a interface
6. Enquanto os aplicativos do celular estão abertos, mesmo em segundo plano,
   eles continuam sincronizando e o PC os vê **online** em `Ferramentas > 🔐
   Sessões de dispositivos`
7. A primeira sincronização mostra uma **barra de progresso** e baixa os dados
   em paralelo e as fotos de 4 em 4

> 🔒 A sincronização é **criptografada (HTTPS)**. O PC cria o próprio
> certificado e a impressão digital dele vai no QR: o celular só se conecta
> *àquele* PC, então ninguém na Wi-Fi consegue ler o tráfego nem se passar por
> ele. Os celulares já vinculados passam sozinhos para HTTPS ao atualizar o app.

### Configuração da rede

Para que a sincronização funcione:

- ✅ O PC e o celular devem estar na **mesma rede Wi-Fi**
- ✅ O **firewall** deve permitir conexões na porta 5000 (ou na configurada)
- ✅ Também deve permitir a **porta seguinte** (5001 por padrão), usada pela conexão criptografada (HTTPS)
- ✅ No Windows, talvez seja preciso criar uma exceção no firewall

### Solução de problemas

**O celular não conecta ao PC:**
- Verifique se os dois dispositivos estão na mesma rede
- Confira se o servidor está ativo no PC (ícone verde)
- Tente desativar temporariamente o firewall do PC
- Gere o código QR novamente e escaneie-o de novo

**Não consigo entrar pelo celular:**
- Confira se o MantPro está aberto no PC: o login é validado nele
- Confirme o usuário e a senha com o administrador; ele pode redefini-la
- Se o PC mudou de IP, escaneie o QR de novo pela própria tela de login ("Vincular outro PC")

**O aplicativo me levou de volta à tela de acesso:**
- É normal se o administrador redefiniu sua senha ou desativou seu usuário
- Seus registros não enviados **não se perdem**: entre de novo e eles serão sincronizados

**Esqueci a senha de administrador:**
- Outro administrador pode redefini-la em `Ferramentas` > `👥 Gerenciamento de usuários`
- Se não houver nenhum outro administrador, é preciso redefini-la diretamente
  na tabela `usuarios` do banco de dados

**As fotos não sincronizam:**
- Verifique se há espaço suficiente no disco do PC
- Confira as permissões da pasta `fotos_recibidas`
- Verifique se a foto foi salva corretamente no celular

**Não recebo a notificação diária de avisos pendentes (Android):**
- Confira se a permissão de notificações está concedida: `Configurações → Apps → MantPro → Notificações`
- Em fabricantes como **OPPO/Realme (ColorOS), Xiaomi (MIUI) ou Huawei**, o sistema pode encerrar o alarme programado mesmo com a permissão concedida. Além disso, é preciso:
  - `Configurações → Bateria → Uso da bateria por app → MantPro` → deixar como **"Sem restrições"**
  - `Configurações → Bateria → Inicialização automática` → **ativar** o MantPro
- A notificação é reavaliada sempre que você abre o Painel; então, se acabou de marcar um serviço como concluído, abra-o de novo para que ela seja cancelada ou reprogramada corretamente.

**Não recebo a notificação diária de conferência de estoque (MantPro Stock):**
- Valem as mesmas verificações do MantPro (permissão de notificações e exclusão da otimização de bateria, veja acima)
- Se o almoxarifado não tiver nenhum material cadastrado, nenhuma notificação é exibida: é o comportamento esperado
- Ela é reavaliada sempre que o aplicativo sincroniza com o PC (ao abrir e a cada 25 segundos enquanto está aberto)

**O MantPro pede uma chave de recuperação ao iniciar:**
- Os bancos de dados estão criptografados e o chaveiro do sistema não tem mais a chave deles (sistema reinstalado, outra conta de usuário…)
- Digite a chave de recuperação que foi mostrada ao ativar a criptografia; o MantPro a guarda de novo no chaveiro
- Se você não a tiver, os bancos de dados não podem ser abertos: tire `mantenimiento.db` e `almacen.db` da pasta de dados, abra o MantPro e restaure uma cópia de segurança

**"Muitas tentativas erradas" ao fazer login:**
- Depois de várias senhas erradas seguidas, o login fica bloqueado por um tempo (15 minutos no celular, um minuto no PC); espere o tempo indicado no aviso ou peça a um administrador para redefinir sua senha

### 🔒 Observação sobre segurança

A sincronização é criptografada com HTTPS e o certificado do PC fica fixado
pela impressão digital do QR. Durante a transição, o PC continua atendendo
também por HTTP na porta configurada para os apps de versões anteriores; o
HTTPS usa a **porta seguinte** (por exemplo, 5000 e 5001), então, se houver um
firewall, é preciso abrir as duas. Se algum dia expuser o servidor fora da rede
local, faça isso por uma VPN.

Quando todos os celulares tiverem o aplicativo atualizado, desative a conexão
sem criptografia em `Ferramentas > 🔐 Sessões de dispositivos`: a coluna
«Criptografia» mostra quais celulares ainda se conectam sem ela. A partir daí o
PC só atende por HTTPS.

Os bancos de dados também podem ser salvos **criptografados** (`Ferramentas >
Criptografia dos bancos de dados…`, SQLCipher): a chave fica no chaveiro do
sistema e é mostrada uma chave de recuperação para você anotar. Vem desativado.

---

## 💾 Cópias de segurança

O MantPro faz uma **cópia automática ao fechar** (os bancos de dados, e as
fotos em ZIP incrementais por ano) e permite fazer uma **cópia completa
manual** em `Arquivo > Backup` e restaurá-la em `Arquivo > Restaurar`.
`Ferramentas` também permite limpar as fotos que nenhum registro usa mais e
excluir os serviços mais antigos que um tempo definido, sempre com cópia
prévia.

🔒 Com `Arquivo > Senha das cópias…` as cópias são salvas **criptografadas**
(AES-256 com uma chave derivada da senha): uma cópia que sai do computador
(pendrive, NAS, nuvem) não pode ser aberta sem ela. Se você esquecer a senha,
as cópias criptografadas não poderão ser recuperadas.

Detalhes completos: [docs/backups.md](docs/backups.md) (em inglês) ·
[docs/copias-de-seguridad.md](docs/copias-de-seguridad.md) (em espanhol).

---

## 🤝 Contribuir

Contribuições são bem-vindas! Antes de abrir um *pull request*, leia o
[CONTRIBUTING.md](CONTRIBUTING.md): ele explica como preparar as alterações
(idiomas, testes, cabeçalhos dos arquivos) e o **acordo de contribuição
([CLA](CLA.md))** que é preciso aceitar.

A estrutura do código e do banco de dados está em
[docs/development.md](docs/development.md) (em inglês) e
[docs/desarrollo.md](docs/desarrollo.md) (em espanhol). Para falhas de
segurança, veja o [SECURITY.md](SECURITY.md).

---

## 🧭 Roteiro

O que vem por aí, sem datas e sem uma ordem fechada:

- **Fornecedores, preços e pedidos de compra** a partir do estoque abaixo do mínimo
- **Assinatura** ao fechar um serviço (também no celular)
- **Documentação técnica por máquina** (manuais, desenhos e esquemas em PDF)
- **Criticidade das máquinas (ABC)**, para decidir onde investir em manutenção
- **Solicitações de serviço** da produção ou de outros departamentos que criam um serviço pendente
- **Notificações push** de serviços urgentes e **vídeos** nos serviços
- **Vários PCs ao mesmo tempo**, servidor sem janela (Raspberry Pi, NAS, Docker) e acesso web
- **Várias unidades ou plantas** com dados e indicadores por unidade
- Mais idiomas (italiano, alemão…) e aplicativo para iPhone

Feito recentemente: preventivas por contador (horas de uso, ciclos, km), tempo trabalhado e custo de mão de obra em cada serviço, peças usadas em cada serviço com seu custo por máquina, checklists em preventivas e serviços, sincronização, bancos de dados e cópias criptografados, e um registro de alterações mais completo.

As mudanças de cada versão estão no [CHANGELOG.md](CHANGELOG.md). Sente falta
de algo? Abra uma [*issue*](https://github.com/AnabasaSoft/MantPro/issues).

---

## 📄 Licença

Este projeto está sob a **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consulte o arquivo `LICENSE` para o texto completo.

Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

### O que isso significa na prática

- ✅ Você pode **usar** o MantPro livremente, inclusive na sua empresa e com fins comerciais
- ✅ Você pode **estudar, modificar e redistribuir** o código
- ⚠️ Se distribuir uma versão modificada, deve publicá-la **também sob AGPL-3.0**
- ⚠️ Se oferecer o MantPro (ou um derivado) **como serviço por meio de uma rede**,
  deve disponibilizar o código-fonte a quem o usar, mesmo que não distribua
  nenhum executável. Essa é a principal diferença em relação à GPL v3
- ⚠️ Você deve manter os avisos de copyright e de licença

### Aviso de licença

```
MantPro - Sistema de Manutenção Preventiva
Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

Este programa é software livre: você pode redistribuí-lo e/ou modificá-lo
sob os termos da Licença Pública Geral Affero GNU, publicada pela Free
Software Foundation, seja a versão 3 da Licença ou (a seu critério)
qualquer versão posterior.

Este programa é distribuído na esperança de que seja útil, mas SEM
NENHUMA GARANTIA; nem mesmo a garantia implícita de COMERCIABILIDADE ou
ADEQUAÇÃO A UMA FINALIDADE ESPECÍFICA. Consulte a Licença Pública Geral
Affero GNU para mais detalhes.

Você deve ter recebido uma cópia da Licença Pública Geral Affero GNU junto
com este programa. Caso contrário, consulte <https://www.gnu.org/licenses/>.
```

> **Observação sobre licenças comerciais**: a AnabasaSoft é a única titular do
> copyright do MantPro e, portanto, pode oferecer o mesmo código em condições
> diferentes da AGPL. Se você precisar integrar o MantPro a um produto
> proprietário, entre em contato.

---

## 📧 Contato

**AnabasaSoft**

- 📧 E-mail: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Projeto: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Agradecimentos

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): framework de interface gráfica multiplataforma para o aplicativo para desktop
- [Flutter](https://flutter.dev/): SDK para os aplicativos para celular
- [ReportLab](https://www.reportlab.com/): geração de relatórios em PDF
- [SQLite](https://www.sqlite.org/): banco de dados embutido
- [Flask](https://flask.palletsprojects.com/): microframework web para o servidor de sincronização
- A comunidade de código aberto, pelo apoio e pelas contribuições

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/recursos/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Desenvolvido com ❤️ por [Anabasa Software](https://anabasasoft.github.io)**

📧 E-mail: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portfólio: [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ Se você gostou deste projeto, dê uma estrela no GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
