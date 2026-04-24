with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

first_order = [
    ('qwen', 'Qwen (Alibaba)'),
    ('deepinfra', 'DeepInfra'),
    ('gemini', 'Google Gemini (Web)'),
    ('grok', 'Grok (xAI)'),
    ('zai-free', 'Z.ai Free (No Auth)'),
    ('kimi', 'Kimi (Moonshot)'),
    ('zai', 'Z.ai (Token)'),
    ('glm', 'GLM (Zhipu)'),
    ('airforce', 'Airforce'),
    ('gradient', 'Gradient Network'),
    ('chat2api', 'Chat2API (Local)'),
    ('lmarena', 'LMArena (Free Models)'),
]

second_order = [
    ('qwen', 'Qwen'),
    ('deepinfra', 'DeepInfra'),
    ('gemini', 'Google Gemini'),
    ('grok', 'Grok (xAI)'),
    ('zai-free', 'Z.ai Free'),
    ('kimi', 'Kimi'),
    ('zai', 'Z.ai (Token)'),
    ('glm', 'GLM (Zhipu)'),
    ('airforce', 'Airforce'),
    ('gradient', 'Gradient Network'),
    ('lmarena', 'LMArena'),
]

out = []
i = 0
while i  len(lines):
    line = lines[i]
    out.append(line)
    if 'id="settings-active-provider"' in line:
        i += 1
        while i  len(lines) and 'option' in lines[i]:
            i += 1
        for val, label in first_order:
            out.append(f'                                option value="{val}">{label}\n')
        out.append(lines[i])
        i += 1
    elif 'id="agent-provider-selector"' in line:
        i += 1
        while i  len(lines) and 'option' in lines[i]:
            i += 1
        for val, label in second_order:
            out.append(f'                                option value="{val}">{label}\n')
        out.append(lines[i])
        i += 1
    else:
        i += 1

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.writelines(out)
print('Done')
