# import streamlit as st
# from vectorstore.build_index import build_index
# from rag.retriever import Retriever
# from rag.generator import Generator
# from dotenv import load_dotenv

# load_dotenv()

# st.set_page_config(page_title="Code Impact Analyzer", layout="wide")

# st.title("🔎 Code Change Impact Analyzer")

# repo_url = st.text_input("Enter GitHub Repo URL")

# # ---------- BUILD INDEX ----------

# if st.button("Build Index"):

#     if not repo_url:
#         st.warning("Please enter a repository URL.")
#     else:
#         with st.spinner("Cloning repo and building embeddings..."):
#             build_index(repo_url)

#         st.success("✅ Index built successfully!")


# # ---------- QUESTION ----------

# question = st.text_input("Ask a question about code impact")


# if st.button("Analyze Impact"):

#     if not question:
#         st.warning("Please enter a question.")
#         st.stop()

#     retriever = Retriever()
#     generator = Generator()

#     with st.spinner("Retrieving relevant code context..."):
#         contexts = retriever.retrieve(question)

#     if not contexts:
#         st.error("❌ No relevant context found in the index.")
#         st.info("Try rebuilding the index.")
#         st.stop()

#     with st.spinner("Analyzing potential impact..."):
#         answer = generator.generate(question, contexts)

#     st.subheader("📊 Impact Analysis")
#     st.write(answer)


#     # ---------- DEBUG VIEW ----------

#     with st.expander("🔍 Retrieved Context (Debug)"):
#         for i, doc in enumerate(contexts):
#             st.markdown(f"**Context {i+1}**")
#             st.code(doc)
import streamlit as st
import os
from vectorstore.build_index import build_index
from rag.retriever import Retriever
from rag.generator import Generator
from analysis.dependency_graph import DependencyGraph
from ingest.commit_loader import CommitLoader
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Code Impact Analyzer", layout="wide")
st.title("🔎 Code Change Impact Analyzer")

# ---------- SESSION STATE ----------
if "graph" not in st.session_state:
    st.session_state.graph = None
if "repo_path" not in st.session_state:
    st.session_state.repo_path = None

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Configuration")
    repo_url = st.text_input("GitHub Repo URL")
    
    if st.button("Build Index"):
        if not repo_url:
            st.warning("Please enter a repository URL.")
        else:
            with st.spinner("Cloning repo and building embeddings..."):
                repo_path = build_index(repo_url)
                
                # Build dependency graph
                graph = DependencyGraph()
                graph.build("temp_repo")
                st.session_state.graph = graph
                st.session_state.repo_path = "temp_repo"
            
            st.success("✅ Index built successfully!")
            st.info(f"📁 Files in dependency graph: {len(graph.graph)}")

    st.divider()
    
    # Show graph stats if built
    if st.session_state.graph:
        st.success("🟢 Index is ready")
        st.metric("Files indexed", len(st.session_state.graph.graph))
    else:
        st.warning("🔴 No index built yet")

# ---------- MAIN TABS ----------
tab1, tab2 = st.tabs(["🔍 Impact Analysis", "📜 Commit History Analysis"])

# ---------- TAB 1: STANDARD RAG ANALYSIS ----------
with tab1:
    question = st.text_input("Describe your code change or ask about impact")

    if st.button("Analyze Impact", key="analyze"):
        if not question:
            st.warning("Please enter a question.")
            st.stop()

        if not st.session_state.graph:
            st.warning("Please build the index first.")
            st.stop()

        retriever = Retriever()
        generator = Generator()

        with st.spinner("Retrieving relevant code context..."):
            contexts = retriever.retrieve(question)

        if not contexts:
            st.error("❌ No relevant context found in the index.")
            st.info("Try rebuilding the index.")
            st.stop()

        # Get dependents from graph
        dependents = []
        graph = st.session_state.graph
        for file in graph.graph.keys():
            if any(keyword.lower() in file.lower() 
                   for keyword in question.split() if len(keyword) > 4):
                found = graph.get_dependents(file)
                dependents.extend(found)
        dependents = list(set(dependents))

        with st.spinner("Analyzing potential impact..."):
            answer = generator.generate(question, contexts, dependents=dependents)

        # ---------- RESULTS ----------
        st.subheader("📊 Impact Analysis")
        st.write(answer)

        # Affected files
        if dependents:
            st.subheader("🔗 Affected Files (Dependency Analysis)")
            for f in dependents:
                st.code(f, language="text")
        else:
            st.info("No direct file dependencies detected for this query.")

        # Debug view
        with st.expander("🔍 Retrieved Context (Debug)"):
            for i, doc in enumerate(contexts):
                st.markdown(f"**Context {i+1}**")
                st.code(doc, language="python")

# ---------- TAB 2: COMMIT HISTORY ANALYSIS ----------
with tab2:
    st.subheader("Analyze impact using recent commit history")
    
    commit_question = st.text_input("Ask about recent changes", 
                                     key="commit_q")
    max_commits = st.slider("Commits to analyze", 5, 50, 20)

    if st.button("Analyze with History", key="commit_analyze"):
        if not commit_question:
            st.warning("Please enter a question.")
            st.stop()

        if not st.session_state.repo_path:
            st.warning("Please build the index first.")
            st.stop()

        try:
            with st.spinner("Loading commit history..."):
                loader = CommitLoader(st.session_state.repo_path)
                commits = loader.get_commits(max_count=max_commits)

            st.info(f"📦 Loaded {len(commits)} commits")

            commit_context = "\n\n".join([
                f"Commit: {c['message'].strip()}\nDiff: {c['diff'][:500]}"
                for c in commits[:5]
            ])

            retriever = Retriever()
            generator = Generator()

            with st.spinner("Retrieving code context..."):
                contexts = retriever.retrieve(commit_question)
                contexts.append(commit_context)

            with st.spinner("Analyzing with commit history..."):
                answer = generator.generate(commit_question, contexts)

            st.subheader("📊 Impact Analysis (with History)")
            st.write(answer)

            # Show recent commits
            with st.expander("📜 Recent Commits Used"):
                for c in commits[:5]:
                    st.markdown(f"**{c['commit_id'][:7]}** — {c['message'].strip()}")
                    st.code(c['diff'][:300], language="diff")

        except Exception as e:
            st.error(f"Error loading commits: {e}")
            st.info("Make sure the repo was cloned locally via Build Index first.")