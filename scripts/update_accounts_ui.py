path = r"f:\autostream-ai\frontend\src\pages\Accounts.jsx"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                    <button onClick={() => onDelete(account.id)} className="btn-danger py-1 px-2" title="Delete Account">
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>"""

replacement = """                    <button onClick={() => onDelete(account.id)} className="btn-danger py-1 px-2" title="Delete Account">
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <Link to={`/workspace/${account.id}`} className="btn-primary py-1 px-3 text-xs flex items-center gap-1">
                        <Layout className="w-3.5 h-3.5" /> Open Workspace
                    </Link>
                </div>"""

content = content.replace(target, replacement)

# Ensure Layout is imported
if "Layout" not in content and "lucide-react" in content:
    content = content.replace("ShieldCheck, Power", "ShieldCheck, Power, Layout")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Accounts.jsx updated.")
