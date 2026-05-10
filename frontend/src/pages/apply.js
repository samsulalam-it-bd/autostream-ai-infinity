const fs = require('fs');
const path = require('path');

const targetPath = 'C:\\Users\\Got it Target\\.gemini\\antigravity\\scratch\\autostream-ai\\frontend\\src\\pages\\UploadZone.jsx';
const newRenderPath = 'C:\\Users\\Got it Target\\.gemini\\antigravity\\scratch\\autostream-ai\\frontend\\src\\pages\\new_UploadZone_render.jsx';

let content = fs.readFileSync(targetPath, 'utf8');
const newRender = fs.readFileSync(newRenderPath, 'utf8');

// 1. Add useState for currentStep
if (!content.includes('const [currentStep, setCurrentStep] = useState(1)')) {
    content = content.replace(
        "const [targetGroupId, setTargetGroupId] = useState('')              // group",
        "const [targetGroupId, setTargetGroupId] = useState('')              // group\n    const [currentStep, setCurrentStep] = useState(1)"
    );
}

// 2. Locate return ( ... )
const searchStrings = [
    '    return (\n        <div className="space-y-6">',
    '    return (\r\n        <div className="space-y-6">',
    '    return (\n'
];

let idx = -1;
for (const s of searchStrings) {
    if (content.indexOf(s) !== -1) {
        idx = content.indexOf(s);
        break;
    }
}

if (idx !== -1) {
    // Replace everything from `return (` down to the end of the file with `newRender`
    // Ensure we close the component bracket
    let finalContent = content.substring(0, idx) + newRender;
    // (Assuming newRender contains the final closing bracket } or we add it)
    if (!finalContent.trim().endsWith('}')) {
        finalContent += '\n}\n';
    }
    fs.writeFileSync(targetPath, finalContent, 'utf8');
    console.log("SUCCESSFULLY PATCHED UPLOADZONE.JSX");
} else {
    console.log("FAILED TO FIND TARGET STRING. First 1000 chars:");
    console.log(content.substring(content.indexOf('return'), content.indexOf('return') + 200));
}
