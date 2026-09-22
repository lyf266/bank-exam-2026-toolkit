#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行从业初级《法律法规》考点 3-1 物权的基本原则和特征 · 结构化母卡生成脚本
依据课件切片与 2024~2026 民法典物权编最新考纲，按“一条一个解释正背面”深度制卡。
"""

import os
import json
import urllib.request

DECK_NAME = "等级考试::银行从业::[理论母卡]初级法律法规"
MODEL_NAME = "问答题"

CARDS_DATA = [
    {
        "front": "<b>【民法典·物权概念】</b>什么是<b>物权</b>？它具有哪两大核心法律特征？客体有什么限定？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>《中华人民共和国民法典》第一百一十四条规定：<b>物权是权利人依法对特定的物享有直接支配和排他的权利。</b></div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>直接支配</b>：权利人无需借助他人的意思或协助，依自身单方意志即可管领、使用或处分标的物以实现其经济利益。</li>
    <li><b>排他性</b>：同一物之上不能并存两个互相冲突的所有权，且排斥他人对该物施加非法干涉或侵占。</li>
    <li><b>客体特定性</b>：物权的标的原则上必须是<b>独立、特定、有体</b>的物（不包括未来的、尚未确定的财产）。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>混淆物权与债权的支配性质——常在单选题中偷换为“物权是请求相对人履行义务的权利”（错！物权是直接支配权，债权才是请求权）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>直接支配排他人，标的须为特定物。
  </div>
</div>"""
    },
    {
        "front": "<b>【民法典·物权分类】</b>我国民法典规定的物权包括哪<b>三大类</b>？何为<b>自物权</b>与<b>他物权</b>？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>物权法定体系分为三大基本类型：</div>
  <ol style="margin: 6px 0; padding-left: 20px;">
    <li><b>所有权（自物权）</b>：所有人对自己的不动产或动产，依法享有<b>占有、使用、收益和处分</b>的全面权利。所有权是唯一完整的自物权，也是物权体系的核心基石。</li>
    <li><b>用益物权（他物权）</b>：对<b>他人所有</b>的不动产或动产，依法享有<b>占有、使用和收益</b>的权利（重在使用价值）。典型包括：建设用地使用权、宅基地使用权、土地承包经营权、<b>居住权（民法典新增）</b>、地役权。</li>
    <li><b>担保物权（他物权）</b>：为确保债务履行，对<b>债务人或第三人的特定财产</b>享有的优先受偿权（重在交换价值）。包括：<b>抵押权、质权、留置权</b>。</li>
  </ol>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>多选题极高频：将“所有权”混入他物权，或将“居住权”误认为担保物权（居住权属于用益物权，满足生活居住需要）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>所有自物权，用益担保他物权。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权 vs 债权①】</b>为什么说<b>“物权是绝对权（对世权）”</b>？与债权有何本质区别？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">⚖️【法理深度辨析】</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权是绝对权（对世权）</b>：物权的权利人是特定的，但<b>义务主体是不特定的世人（任何人）</b>。除物权人之外，世上任何不特定第三人都负有“不得侵犯、不得妨害”其行使权利的消极不作为义务。</li>
    <li><b>债权是相对权（对人权）</b>：债权的权利主体与义务主体<b>都是特定的</b>。债权人只能依据合同或法定事由，向特定的债务人请求给付，不能直接要求第三人承担合同义务（合同相对性）。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>判断题常设陷阱：“债权具有对世效力，可以对抗除债务人以外的任何第三人”（错！债权仅具对人相对性，物权才具有对世效力）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>物权对世抗全员，债权对人限特定。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权 vs 债权②】</b>为什么说<b>“物权是支配权”</b>？与债权的“请求权”属性有何不同？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">⚖️【法理深度辨析】</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权是支配权</b>：物权人仅凭<b>单方的意志和直接的管领行为</b>，即可支配标的物并实现权利，<b>不需要义务人的积极行为相配合</b>。任何人的不当干预都构成侵权。</li>
    <li><b>债权是请求权</b>：债权人不能直接支配债务人的财产，其利益的实现<b>必须依赖于债务人的主动给付行为</b>（如还款、交付商品）。若债务人违约不履行，债权人只能提起诉讼或仲裁申请强制执行，不得私力抢夺。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>银行借贷实务题眼：银行享有贷款债权，不能在借款人逾期后直接擅自开走借款人名下无抵押的车辆，必须经诉讼与司法执行程序，正是因为“债权是请求权而非支配权”。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>物权单方直支配，债权依赖彼给付。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权 vs 债权③】</b><b>物权的标的（客体）</b>与<b>债权的标的</b>有何本质差异？劳务能否成为物权客体？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">⚖️【法理深度辨析】</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权的标的（客体）必须是“物”</b>：包括不动产（土地、房屋）和动产（车辆、设备）。法律规定权利作为物权客体的除外（如权利质押客体为汇票、股权等）。<b>“劳务”或“纯粹行为”绝不能成为物权的标的</b>。</li>
    <li><b>债权的标的（客体）是“行为（给付）”</b>：包括作为（如付款、交付特定物、提供技术服务）和不作为（如竞业禁止守约行为）。标的物只是给付行为所指向的对象。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>判断题题眼：“物权与债权的标的都是特定的有体物”（错！物权标的是物，债权标的是行为/给付）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>物权标的为有物，债权标的在给付。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权 vs 债权④】</b>为什么说<b>“物权具有排他性”</b>，而债权具有<b>“相容性与平等性”</b>？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">⚖️【法理深度辨析】</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权具有排他性</b>：同一物之上<b>不得同时设立两个互不相容的物权</b>。例如：同一辆车不能同时归甲、乙两人各自独占所有（一物一权）；设立了完全独占建设用地使用权的地块不能再设另一重叠使用权。</li>
    <li><b>债权具有相容性与平等性</b>：同一标的物之上<b>可以同时成立数个内容相同的债权</b>（典型如“一房数卖”成立的多个买卖合同均有效）。各个债权人在法律地位上完全平等，成立在先的债权并不享有法定的优先受偿地位，普通债权平等按比例受偿。</li>
    <li><b>衍生规则（物权优先于债权）</b>：同一财产上物权与债权并存时，物权原则上优先于普通债权受偿（如抵押权人优先于无担保债权人）。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>单选/多选题考查“一房数卖”：合同因债权相容性均有效，但最终取得房屋物权所有权（完成不动产过户登记）的人优先排斥其他债权人的给付请求。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>一物不容二所有，数重债权俱平等。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权 vs 债权⑤】</b>什么是<b>物权的“追及力”</b>？其在法律上的核心阻断例外是什么？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">⚖️【法理深度辨析】</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权具有追及力（追及效力）</b>：物权的标的物不论辗转落入何人之手，除法律另有特殊规定外，<b>物权人均得追及至标的物所在之处，向非法占有人请求返还原物</b>。而债权无追及力，标的物一旦被第三人占有，债权人只能向债务人主张违约或侵权赔偿，不能直接向第三人主张返还。</li>
    <li><b>追及力的法定阻断例外 ——【善意取得制度】</b>：
      无处分权人将动产或不动产转让给他人，受让人若同时满足以下 3 项条件，依法即时取得物权，<b>原物权人的追及力被依法切断</b>：
      ① 受让人受让该不动产或动产时是<b>善意</b>的；
      ② 以<b>合理的价格</b>受让（有偿交易）；
      ③ 转让的不动产或者动产依照法律规定<b>已经登记或者交付</b>给受让人。
      （原物权人此时只能向无处分权人追偿损失，不得向善意受让人请求返还原物）。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>判断题陷阱：“物权的追及力具有绝对性，在任何情形下原所有人均能强制追回原物”（错！善意取得制度将切断追及力）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>物落何处皆可追，善意取得阻断回。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权基本原则①】</b>什么是物权的<b>平等保护原则</b>？在我国现行民法体系中如何体现？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>《民法典》第二百零七条确立了平等保护原则：<b>国家、集体、私人的物权和其他权利人的物权受法律平等保护，任何组织或者个人不得侵犯。</b></div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>民事主体地位平等</b>：在民事流转与物权确认中，国家作为民事主体时与民营企业、普通公民处于同等的法律地位，享有同等的权利保护。</li>
    <li><b>侵权责任与救济统一</b>：侵犯任何主体的物权，均依照民法典承担相同的停止侵害、排除妨碍、赔偿损失等民事责任，严禁差别救济。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>陈旧观念陷阱：认为国有金融机构或国有资产在民事纠纷中享有超越民法的优先救济特权（错！《民法典》严格恪守各类物权一律受法律平等保护原则）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>国集私财皆平等，同规同责同保护。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权基本原则②】</b>什么是<b>物权法定原则</b>？“法定”包含哪两个维度？当事人协议创设是否有效？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>《民法典》第一百一十六条规定：<b>物权的种类和内容，由法律规定。</b></div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>物权种类法定</b>：民事主体只能在全国人大及其常委会颁布的法律明文规定的范围内设定物权类型，<b>当事人不得自行协议创设法律未规定的新物权类型</b>（禁止物权创设自由）。</li>
    <li><b>物权内容法定</b>：物权人享有哪些具体权能、权利行使的界限以及法律限制，由法律直接规定，<b>当事人不得通过私人约定随意予以排除或变更</b>。</li>
    <li><b>效力认定</b>：当事人在合同中约定创设未法定物权类型的，<b>不发生物权效力</b>，但合同本身符合生效要件的依然发生合同债权效力。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>强烈对比题眼：合同领域奉行<b>“契约自由原则”</b>（只要不违背公序良俗和法律强制性规定即可自由约定），而物权领域奉行<b>“物权法定原则”</b>，绝对禁止任意创设！</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>种类内容由法设，私约禁止创物权。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权基本原则③】</b>什么是<b>一物一权原则</b>？同一物之上能否并存抵押权或用益物权？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>一物一权原则包含两层核心法理含义：</div>
  <ol style="margin: 6px 0; padding-left: 20px;">
    <li><b>一个所有权客体为一个独立物</b>：一个物权的客体只能是一个独立的特定物，物的一部分不能单独设立独立的所有权。</li>
    <li><b>一物之上只容纳一个所有权</b>：同一特定物之上，<b>绝对不能同时成立两个互不相容、内容相同的所有权</b>（一物不容二主）。</li>
  </ol>
  <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 6px 10px; margin: 8px 0; border-radius: 4px;">
    <b>🔍【相容并存法则（机考核心考核点）】</b>
    <ul style="margin: 4px 0; padding-left: 18px;">
      <li>同一物之上<b>可以</b>在所有权之上设定他物权（如房产上设定居住权或抵押权）；</li>
      <li>同一财产之上<b>可以</b>依法设立多个不同顺位的抵押权（余额抵押）；</li>
      <li>“一物一权”是指<b>一物之上只能有一个所有权</b>，绝非指一物之上只能有一个物权！</li>
    </ul>
  </div>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>判断题高发坑点：“依据一物一权原则，已经设立抵押权的房产不得再行设立第二顺位抵押”（错！只要价值允许，可以设立多顺位抵押）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>一物唯一所有权，担保用益可并存。
  </div>
</div>"""
    },
    {
        "front": "<b>【物权基本原则④】</b>什么是<b>公示原则</b>与<b>公信原则</b>？不动产与动产的法定公示方式分别是什么？",
        "back": """<div style="font-family: 'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC', sans-serif; line-height: 1.55;">
  <div style="font-weight: bold; color: #1e3a8a; font-size: 15px; margin-bottom: 6px;">💡【核心考点精释】</div>
  <div>物权作为支配权和排他权，必须有让外界可明确感知的客观外部表征：</div>
  <ul style="margin: 6px 0; padding-left: 20px;">
    <li><b>1. 公示原则（权属外部公开化）</b>：物权的设立、变更、转让和消灭，必须依照法定的公开方式向社会公示：
      <ul>
        <li>🏠 <b>不动产物权</b>：以<b>【登记】</b>为法定公示方式（不动产物权的设立经依法登记发生效力，未经登记不发生效力，法律另有规定除外）。</li>
        <li>🚗 <b>动产物权</b>：以<b>【交付】</b>（转移占有）为法定公示方式（动产物权自交付时发生效力）。</li>
      </ul>
    </li>
    <li><b>2. 公信原则（信赖外观受保护）</b>：物权公示所表现出的权利状态，哪怕与真实的权利状态不符（如不动产权属证书登记出现笔误），<b>善意信赖该登记或交付外观并进行了交易的第三人，其所取得的权利依然受到法律完全保护</b>（善意取得制度的理论依据）。</li>
  </ul>
  <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 6px 10px; margin: 8px 0; border-radius: 2px;">
    <b>⚠️【机考高频避坑】</b>
    <div>区分公示与公信：公示解决的是“用什么方式让别人知道权利归属”（登记或交付）；公信解决的是“别人相信了这个外观后法律保护谁”（保护善意第三人）。</div>
  </div>
  <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 6px 10px; margin-top: 6px; border-radius: 2px;">
    <b>🔑【15字黄金速记口诀】</b>不动产登记动产交，善意信赖受公信。
  </div>
</div>"""
    }
]

def anki_invoke(action, **params):
    req = urllib.request.Request(
        "http://127.0.0.1:8765",
        json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if len(res) == 2 and "error" in res and res["error"] is not None:
            raise Exception(res["error"])
        return res["result"]

def main():
    print(f"🚀 正在向牌组 '{DECK_NAME}' 注入考点 3-1 物权结构化母卡...")
    notes = []
    for item in CARDS_DATA:
        notes.append({
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": {
                "正面": item["front"],
                "背面": item["back"]
            },
            "tags": ["2026银行从业", "初级法律法规", "民法典物权编", "考点3-1物权原则和特征"]
        })
    
    added_ids = anki_invoke("addNotes", notes=notes)
    success = sum(1 for x in added_ids if x is not None)
    print(f"✅ 成功注入 {success} / {len(notes)} 张卡片！")
    
    # 重新导出离线包
    base_dir = "/home/f1are/orca/workspaces/银行从业备考/anki"
    export_main = os.path.join(base_dir, "2026银行从业初级_全真机考客观题.apkg")
    export_all = os.path.join(base_dir, "2026银行从业初级_全真套题全量卡包.apkg")
    anki_invoke("exportPackage", deck="等级考试::银行从业", path=export_main, includeSched=False)
    anki_invoke("exportPackage", deck="等级考试::银行从业", path=export_all, includeSched=False)
    print("📦 离线包已同步更新！")

if __name__ == "__main__":
    main()
