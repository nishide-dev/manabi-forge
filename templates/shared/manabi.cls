%% manabi.cls — Manabi Forge 共有ベースクラス(spec §15)
%% テンプレートは視覚構造のみを所有し、教科の内容は教材ソースが所有する。
%% ライセンス: Apache-2.0(リポジトリルートの LICENSE-CODE)
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{manabi}[2026/08/16 v0.1.0 Manabi Forge base class]

%% テンプレートオプション: 対応する manabi-<template>.sty を読み込む。
%% 各テンプレートの .sty は templates/<template>/ に置かれ、TEXINPUTS で解決される。
\newif\ifmanabi@guidedexample
\DeclareOption{guided-example}{\manabi@guidedexampletrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ltjsarticle}}
\ProcessOptions\relax

\LoadClass[a4paper,10pt]{ltjsarticle}

%% --- 基本パッケージ -------------------------------------------------------
\RequirePackage[
  a4paper,
  margin=18mm,
  top=24mm,
  bottom=28mm,
  headheight=16pt,
  footskip=32pt,
]{geometry}
%% フォントは TeX Live 同梱の原ノ味(プロプライエタリフォント禁止: spec §9.4)
\RequirePackage[haranoaji]{luatexja-preset}
\RequirePackage{amsmath,amssymb}
\RequirePackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\RequirePackage{enumitem}
\RequirePackage{fancyhdr}
\RequirePackage{hyperref}
\hypersetup{hidelinks,unicode}
\RequirePackage{bookmark}

%% --- 教材メタデータ --------------------------------------------------------
%% manabi tex build(将来)または教材ソース冒頭で設定する。
\newcommand*\manabi@id{unset-id}
\newcommand*\manabi@version{0.0.0}
\newcommand*\manabi@title{}
\newcommand*\manabi@course{}
\newcommand*\manabi@unit{}
\newcommand*\manabi@difficulty{}
\newcommand*\manabi@minutes{}
\newcommand*\manabi@contentlicense{CC BY 4.0}
\newcommand*\ManabiId[1]{\renewcommand*\manabi@id{#1}}
\newcommand*\ManabiVersion[1]{\renewcommand*\manabi@version{#1}}
\newcommand*\ManabiTitle[1]{\renewcommand*\manabi@title{#1}}
\newcommand*\ManabiCourse[1]{\renewcommand*\manabi@course{#1}}
\newcommand*\ManabiUnit[1]{\renewcommand*\manabi@unit{#1}}
\newcommand*\ManabiDifficulty[1]{\renewcommand*\manabi@difficulty{#1}}
\newcommand*\ManabiMinutes[1]{\renewcommand*\manabi@minutes{#1}}
\newcommand*\ManabiContentLicense[1]{\renewcommand*\manabi@contentlicense{#1}}

%% テンプレート識別(成果物はテンプレート ID とバージョンを記録する: spec §15.3)
\newcommand*\manabi@templatename{shared}
\newcommand*\manabi@templateversion{0.1.0}
\newcommand*\ManabiTemplate[2]{%
  \renewcommand*\manabi@templatename{#1}%
  \renewcommand*\manabi@templateversion{#2}}

%% --- 免責事項(spec §4.3、全公開物に必須) --------------------------------
\newcommand*\ManabiDisclaimer{%
  この教材は Manabi Forge contributors が独自に制作した非公式教材です。%
  文部科学省、大学入試センター、教科書会社、参考書出版社その他の団体による%
  公式教材ではありません。}

%% --- ヘッダ・フッタ --------------------------------------------------------
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\sffamily \manabi@title}
\fancyhead[R]{\small\ttfamily \manabi@id\ v\manabi@version}
\fancyfoot[C]{\parbox{0.92\textwidth}{\centering\scriptsize \ManabiDisclaimer\\%
  ライセンス: \manabi@contentlicense\quad
  テンプレート: \manabi@templatename\ v\manabi@templateversion}}
\fancyfoot[R]{\small \thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.2pt}

%% --- タイトルブロック ------------------------------------------------------
\newcommand*\ManabiMakeTitle{%
  \begin{center}
    {\LARGE\bfseries \manabi@title\par}
    \vspace{4pt}
    {\small
      \manabi@course
      \ifx\manabi@unit\empty\else \quad|\quad \manabi@unit\fi
      \ifx\manabi@difficulty\empty\else \quad|\quad 難易度:~\manabi@difficulty\fi
      \ifx\manabi@minutes\empty\else \quad|\quad 目安時間:~\manabi@minutes 分\fi
      \par}
  \end{center}
  \vspace{6pt}}

%% --- PDF メタデータ --------------------------------------------------------
\AtBeginDocument{%
  \hypersetup{%
    pdftitle={\manabi@title\ (\manabi@id)},%
    pdfauthor={Manabi Forge contributors},%
    pdfsubject={Manabi Forge learning material},%
  }}

%% --- テンプレート読み込み(最後に行い、クラス定義を利用可能にする) --------
\ifmanabi@guidedexample
  \RequirePackage{manabi-guided-example}
\fi

\endinput
