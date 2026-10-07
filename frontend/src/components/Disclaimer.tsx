// 모든 결과 화면 하단에 붙는 면책 문구 + 상담 연결
export default function Disclaimer() {
  return (
    <aside className="space-y-2 rounded-xl border border-line bg-white p-4 text-xs leading-relaxed text-sub">
      <p>
        이 결과는 <strong className="text-text">참고용 확인 정보이며 법적 판단이 아닙니다.</strong>{" "}
        판정은 정해진 규칙이 하고, AI는 문서를 읽는 데만 쓰여요. 각 항목의 원문 문구와 근거 조문을 함께
        확인해 주세요.
      </p>
      <p>
        정확한 판단이 필요하면 고용노동부 고객상담센터{" "}
        <a href="tel:1350" className="font-bold text-primary underline">
          ☎ 1350
        </a>{" "}
        또는 공인노무사 상담을 이용해 주세요.
      </p>
    </aside>
  );
}
