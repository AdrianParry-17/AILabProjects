import { motion } from "framer-motion";
import { BookOpen, CheckCircle2, Compass, FlaskConical, FunctionSquare, ShieldCheck, Sparkles, XCircle } from "lucide-react";
import type { MetadataPayload } from "../types";

export function AlgorithmGuide({ metadata }: { metadata: MetadataPayload }) {
  return (
    <main className="learn-layout">
      <section className="learn-hero panel">
        <div>
          <span className="section-kicker">INTERACTIVE THEORY DECK</span>
          <h2>Search algorithms, nhìn từ một con đường thật</h2>
          <p>Mỗi thuật toán nhận cùng directed graph và trả cùng result contract. Sự khác biệt nằm ở cách frontier được tổ chức, cost nào được nhìn thấy, và có dùng ước lượng tới goal hay không.</p>
        </div>
        <div className="formula-orb">
          <FunctionSquare size={25} />
          <strong>C(e) = w<sub>d</sub>D + w<sub>t</sub>T + w<sub>c</sub>C + w<sub>r</sub>R</strong>
          <small>Mọi thành phần không âm • road closure bị loại khỏi graph</small>
        </div>
      </section>

      <section className="algorithm-card-grid">
        {metadata.algorithms.map((item, index) => {
          const optimality = String(item.optimal).toLowerCase();
          const optimal = item.optimal === true || optimality.startsWith("optimal for");
          const conditionalOptimal = optimality.startsWith("optimal with");
          const complete = item.complete === true || String(item.complete).toLowerCase().includes("yes");
          return (
            <motion.article
              key={item.id}
              className="algorithm-card panel"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(index * 0.04, 0.3) }}
            >
              <div className="algorithm-index">{String(index + 1).padStart(2, "0")}</div>
              <div className="algorithm-family">{item.family || (item.supports_heuristic ? "INFORMED" : "UNINFORMED / COST")}</div>
              <h3>{item.name}</h3>
              <p>{item.description}</p>
              <div className="algorithm-properties">
                <span className={complete ? "yes" : "no"}>{complete ? <CheckCircle2 size={13} /> : <XCircle size={13} />} Complete</span>
                <span className={optimal ? "yes" : conditionalOptimal ? "conditional" : "no"}>
                  {optimal ? <ShieldCheck size={13} /> : <Compass size={13} />}
                  {optimal ? "Optimal" : conditionalOptimal ? "Conditional" : "Not optimal"}
                </span>
                {item.supports_heuristic && <span className="heuristic"><Sparkles size={13} /> heuristic</span>}
              </div>
              <dl>
                <div><dt>Time</dt><dd>{item.complexity_time || "phụ thuộc graph"}</dd></div>
                <div><dt>Space</dt><dd>{item.complexity_space || "phụ thuộc frontier"}</dd></div>
              </dl>
              {item.caveat && <small className="caveat">{item.caveat}</small>}
            </motion.article>
          );
        })}
      </section>

      <section className="theory-lower-grid">
        <article className="panel heuristic-table-card">
          <div className="panel-heading compact"><div><span className="section-kicker">HEURISTIC REGISTRY</span><h2>Độ tin cậy của h(n)</h2></div><Sparkles size={20} /></div>
          <div className="heuristic-list">
            {metadata.heuristics.map((item) => (
              <div key={item.id}>
                <span><strong>{item.name}</strong><small>{item.description}</small></span>
                <span className={item.admissible === true ? "safe" : "practical"}>{item.admissible === true ? "admissible" : "practical"}</span>
                <span className={item.consistent === true ? "safe" : "practical"}>{item.consistent === true ? "consistent" : "conditional"}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel lab-rules-card">
          <div className="panel-heading compact"><div><span className="section-kicker">EXPERIMENT DISCIPLINE</span><h2>So sánh không đánh tráo</h2></div><FlaskConical size={20} /></div>
          <ul>
            <li><CheckCircle2 size={15} /> Cùng graph snapshot và một chiều đường.</li>
            <li><CheckCircle2 size={15} /> Cùng traffic scenario và custom weights.</li>
            <li><CheckCircle2 size={15} /> Runtime chỉ đo search, không đo animation/API.</li>
            <li><CheckCircle2 size={15} /> Tie-breaking cố định để demo lặp lại được.</li>
            <li><CheckCircle2 size={15} /> Traffic/flood là synthetic layer, không phải live data.</li>
          </ul>
          <div className="source-note"><BookOpen size={15} /> Road topology derived from OpenStreetMap; educational traffic estimates are documented separately.</div>
        </article>
      </section>
    </main>
  );
}
