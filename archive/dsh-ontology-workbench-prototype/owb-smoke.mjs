import { loadWorkspace, listModelFiles } from './owb-dist/engine/yamlStore.js';
import { validateWorkspace, buildGraphData } from './owb-dist/engine/graphData.js';
import { createApp, summarize } from './owb-dist/engine/appRuntime.js';

const dir = 'D:/sharptoolbox/Onto-Model/sample';
console.log('模型文件:', listModelFiles(dir).map(f=>f.file+'('+(f.model_type||'?')+')').join(', '));
const { models } = loadWorkspace(dir);
console.log('加载模型 keys:', Object.keys(models).join(', '));
const issues = validateWorkspace(models);
console.log('校验 issues:', issues.length, issues.slice(0,3).map(i=>i.code).join(','));
const g = buildGraphData(models);
console.log('图谱 nodes:', g.nodes.length, 'edges:', g.edges.length, '| cats:', [...new Set(g.nodes.map(n=>n.cat))].join(','));
const db = createApp(models.objectModel);
console.log('建表:', db.tables.join(', '));
console.log('各表行数:', JSON.stringify(summarize(db.db, db.specs)));
