<template>
  <div class="page-section">
    <h1 class="page-title">{{ isEdit ? '테스트 수정' : '테스트 생성' }}</h1>
    <UiProgress v-if="loading" indeterminate class="mb-2" />
    <UiAlert v-else-if="loadError" type="error" class="mb-2">{{ loadError }}</UiAlert>
    <form v-else @submit.prevent="onSubmit" class="test-form compact-form">
      <div class="vf-row vf-row--dense align-center mb-2 form-row-nowrap-sm">
        <div class="vf-col vf-col-12 vf-col-sm-5 vf-col-md-4 field-col-shrink">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model="form.name"
              required
              hide-details="auto"
              :error-messages="errors.name ? [errors.name] : []"
              label="테스트 이름"
              class="flex-grow-1"
            />
            <UiTooltip text="나중에 구분하기 위한 이름입니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-12 vf-col-sm-7 vf-col-md-8 d-flex align-center flex-nowrap ga-3 engine-col">
          <span class="text-body-2 text-medium-emphasis flex-shrink-0 d-none d-sm-inline">실행 방식</span>
          <div class="radio-inline engine-radio flex-grow-1">
            <label>
              <input v-model="form.engine" type="radio" value="http" />
              k6 (HTTP)
            </label>
            <label>
              <input v-model="form.engine" type="radio" value="browser" />
              브라우저 (렌더링)
            </label>
            <label>
              <input v-model="form.engine" type="radio" value="db" />
              DB 쿼리
            </label>
          </div>
        </div>
      </div>

      <div class="vf-row vf-row--dense align-start mb-2">
        <div class="vf-col vf-col-12">
          <div class="d-flex align-start gap-1">
            <div class="flex-grow-1" style="min-width: 0">
              <p v-if="form.tags.length" class="tags-chips d-flex flex-wrap gap-1 mb-2">
                <UiChip
                  v-for="(tg, ti) in form.tags"
                  :key="ti + '-' + tg"
                  closable
                  :color="tagColorKey(tg)"
                  @click:close="removeTag(ti)"
                >
                  {{ tg }}
                </UiChip>
              </p>
              <div class="tag-input-wrap">
                <UiTextField
                  v-model="tagDraft"
                  label="태그"
                  placeholder="기존 태그 검색 또는 새 태그 · Enter"
                  hide-details="auto"
                  hint="다른 테스트에 쓰인 태그가 제안됩니다. 새 이름은 그대로 입력해 추가할 수 있습니다. 태그당 최대 32자, 최대 32개."
                  @focus="onTagFocus"
                  @blur="onTagInputBlur"
                  @keydown.enter.prevent="onTagEnter"
                  @keydown.down.prevent="onTagArrowDown"
                  @keydown.up.prevent="onTagArrowUp"
                  @keydown.escape="tagPanelOpen = false"
                />
                <ul
                  v-show="tagPanelOpen && filteredSuggestions.length"
                  class="tag-suggest-list"
                  role="listbox"
                >
                  <li
                    v-for="(s, idx) in filteredSuggestions"
                    :key="s"
                    role="option"
                    :aria-selected="idx === tagHighlightIndex"
                    class="tag-suggest-list__item"
                    :class="{ 'tag-suggest-list__item--active': idx === tagHighlightIndex }"
                    @mousedown.prevent="selectSuggestion(s)"
                  >
                    {{ s }}
                  </li>
                </ul>
              </div>
            </div>
            <UiTooltip text="테스트 목록에서 같은 태그로 묶어 찾을 수 있습니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
      </div>

      <div v-if="form.engine === 'http'" class="vf-row vf-row--dense align-center mb-2 form-row-nowrap-sm checkbox-options-row">
        <div class="vf-col vf-col-12 checkbox-help-row">
          <UiCheckbox v-model="form.vuUrlSuffix" label="경로 끝에 VU 번호 붙이기" class="checkbox-help-row__check" />
          <UiTooltip
            text="예: /a/b/ccc → /a/b/ccc1, ccc2. 각 HTTP 단계 URL에 적용됩니다."
            class="checkbox-help-row__tip"
          >
            <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
          </UiTooltip>
        </div>
      </div>

      <div v-if="form.engine === 'browser'" class="vf-row vf-row--dense align-center mb-2 form-row-nowrap-sm">
        <div class="vf-col vf-col-12 vf-col-sm-3 vf-col-md-2 flex-shrink-0">
          <div class="d-flex align-start gap-1">
            <UiSelect
              v-model="form.httpMethod"
              :items="['GET', 'POST', 'PUT', 'PATCH', 'DELETE']"
              hide-details
              label="HTTP 메서드"
              class="flex-grow-1"
            />
            <UiTooltip text="요청 방식입니다. 보통 조회는 GET, 데이터 전송은 POST를 씁니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-12 vf-col-sm-9 vf-col-md-10" style="min-width: 0">
          <div class="d-flex align-start gap-1">
            <UiTextField
              :model-value="urlDisplay"
              placeholder="https://…"
              hide-details="auto"
              :error-messages="errors.baseUrl ? [errors.baseUrl] : []"
              label="대상 URL"
              class="flex-grow-1"
              @update:model-value="onUrlDisplayInput"
              @blur="parseUrlAndSyncToParams"
            />
            <UiTooltip :text="'부하를 줄 주소입니다. VU별로 다르게 하려면 경로에 ' + vuPlaceholder + ' 를 넣거나 위 옵션을 사용하세요.'">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
      </div>

      <div v-if="form.engine === 'db'" class="vf-row vf-row--dense mb-2">
        <div class="vf-col vf-col-12 vf-col-sm-3 vf-col-md-2 flex-shrink-0 mb-2">
          <UiSelect
            v-model="form.dbDriver"
            :items="['postgres']"
            hide-details
            label="DB 드라이버"
          />
        </div>
        <div class="vf-col vf-col-12 vf-col-sm-9 vf-col-md-10 mb-2" style="min-width: 0">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model="form.baseUrl"
              placeholder="postgres://user:pass@host:5432/dbname?sslmode=disable"
              hide-details="auto"
              :error-messages="errors.baseUrl ? [errors.baseUrl] : []"
              label="연결 문자열 (DSN)"
              class="flex-grow-1"
            />
            <UiTooltip text="xk6-sql이 접속할 DB 연결 문자열입니다. 자격증명이 그대로 저장되니 주의하세요.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-12">
          <UiTextarea
            v-model="form.dbQuery"
            label="SQL 쿼리"
            placeholder="SELECT * FROM users WHERE id = 1;"
            rows="4"
            auto-grow
            hide-details="auto"
            :error-messages="errors.dbQuery ? [errors.dbQuery] : []"
          />
          <p class="text-caption text-medium-emphasis mt-1 mb-0">
            VU마다 이 쿼리를 반복 실행해 실행 시간·TPS·실패율을 측정합니다.
          </p>
        </div>
      </div>

      <div v-if="form.engine === 'http'" class="vf-row vf-row--dense mt-2">
        <div class="vf-col vf-col-12">
          <p class="text-subtitle-2 mb-2">HTTP 단계</p>
          <UiAlert type="info" class="mb-2 scenario-flow-hint">
            단계가 1개면 기존 단일 요청과 같습니다. «단계 추가»로 여러 단계를 이어 실행할 수 있고, 캡처 탭으로 이전 응답 값을 다음 단계에 넣을 수 있습니다.
          </UiAlert>
          <div
            v-for="(step, si) in scenarioSteps"
            :key="si"
            class="mb-3 pa-3 scenario-step-card"
          >
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-body-2 font-weight-medium">단계 {{ si + 1 }}</span>
              <UiBtn
                icon
                variant="text"
                color="error"
                :disabled="scenarioSteps.length <= 1"
                @click="removeScenarioStep(si)"
              >
                <UiIcon icon="mdi-delete-outline" size="small" />
              </UiBtn>
            </div>
            <div class="scenario-step-request-block mb-3">
              <div class="vf-row vf-row--dense">
                <div class="vf-col vf-col-12 vf-col-md-6 vf-col-lg-4">
                  <UiTextField
                    v-model="step.name"
                    label="단계 이름 (선택)"
                    placeholder="login"
                    hide-details="auto"
                  />
                </div>
              </div>
              <div class="vf-row vf-row--dense form-row-nowrap-sm">
                <div class="vf-col vf-col-12 vf-col-sm-3 vf-col-md-2 flex-shrink-0">
                  <UiSelect
                    v-model="step.method"
                    :items="['GET', 'POST', 'PUT', 'PATCH', 'DELETE']"
                    label="메서드"
                    hide-details
                  />
                </div>
                <div class="vf-col vf-col-12 vf-col-sm-9 vf-col-md-10 scenario-step-url-col">
                  <UiTextField
                    v-model="step.url"
                    label="URL (쿼리는 아래 Params 탭)"
                    placeholder="https://…/v1/…"
                    hide-details="auto"
                    :error-messages="errors.scenarioUrls && errors.scenarioUrls[si] ? [errors.scenarioUrls[si]] : []"
                  />
                </div>
              </div>
              <div class="vf-row vf-row--dense mt-1">
                <div class="vf-col vf-col-12 vf-col-sm-6 vf-col-md-4">
                  <UiTextField
                    v-model="step.sleepAfterSeconds"
                    label="다음 스텝 전 대기(초)"
                    type="number"
                    min="0"
                    max="600"
                    step="0.1"
                    hide-details="auto"
                    hint="0 또는 비움 = 스텝 간 대기 없음. 이 단계 응답·기록 직후 적용."
                  />
                </div>
              </div>
            </div>
            <div class="ui-tabs scenario-step-tabs mb-2" role="tablist">
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'params' }"
                @click="step.scenarioTab = 'params'"
              >
                Params
              </button>
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'headers' }"
                @click="step.scenarioTab = 'headers'"
              >
                Headers
              </button>
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'body' }"
                @click="step.scenarioTab = 'body'"
              >
                Body
              </button>
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'poll' }"
                @click="step.scenarioTab = 'poll'"
              >
                폴링
              </button>
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'capture' }"
                @click="step.scenarioTab = 'capture'"
              >
                캡처
              </button>
              <button
                type="button"
                class="ui-tabs__btn"
                :class="{ 'ui-tabs__btn--active': step.scenarioTab === 'error' }"
                @click="step.scenarioTab = 'error'"
              >
                에러 판별
              </button>
            </div>
            <div class="scenario-step-window">
              <div v-show="step.scenarioTab === 'params'">
                <div class="kv-section">
                  <div v-for="(row, pi) in step.paramsList" :key="pi" class="kv-row">
                    <UiCheckbox v-model="row.enabled" class="param-check flex-shrink-0" />
                    <UiTextField v-model="row.key" placeholder="Key" hide-details class="kv-key" />
                    <UiTextField
                      v-model="row.value"
                      :placeholder="'Value (VU별: ' + vuPlaceholder + ')'"
                      hide-details
                      class="kv-value"
                    />
                    <UiBtn
                      icon
                      variant="text"
                      color="error"
                      :disabled="step.paramsList.length <= 1"
                      @click="removeScenarioParam(si, pi)"
                    >
                      <UiIcon icon="mdi-delete-outline" size="small" />
                    </UiBtn>
                  </div>
                  <UiBtn variant="outlined" class="mt-1" @click="addScenarioParam(si)">추가</UiBtn>
                </div>
              </div>
              <div v-show="step.scenarioTab === 'headers'">
                <div class="kv-section">
                  <div v-for="(row, hi) in step.headersList" :key="hi" class="kv-row">
                    <UiCheckbox v-model="row.enabled" class="param-check flex-shrink-0" />
                    <UiTextField v-model="row.key" placeholder="Key" hide-details class="kv-key" />
                    <UiTextField
                      v-model="row.value"
                      :placeholder="'Value (VU별: ' + vuPlaceholder + ')'"
                      hide-details
                      class="kv-value"
                    />
                    <UiBtn
                      icon
                      variant="text"
                      color="error"
                      :disabled="step.headersList.length <= 1"
                      @click="removeScenarioHeader(si, hi)"
                    >
                      <UiIcon icon="mdi-delete-outline" size="small" />
                    </UiBtn>
                  </div>
                  <UiBtn variant="outlined" class="mt-1" @click="addScenarioHeader(si)">헤더 추가</UiBtn>
                </div>
              </div>
              <div v-show="step.scenarioTab === 'body'">
                <UiSelect
                  v-model="step.bodyKind"
                  :items="scenarioBodyKindItems"
                  item-title="title"
                  item-value="value"
                  label="본문 유형"
                  class="mb-2"
                  hide-details
                  @update:model-value="(v) => onScenarioBodyKindChange(step, v)"
                />
                <div v-if="step.bodyKind === 'raw'" class="textarea-col">
                  <UiTextarea
                    v-model="step.body"
                    :placeholder="'요청 본문. VU별: ' + vuPlaceholder + ' 삽입 가능'"
                    rows="4"
                    hide-details
                  />
                </div>
                <div v-else class="scenario-multipart-block">
                  <UiAlert type="info" class="mb-2 scenario-multipart-hint">
                    파일은 API 서버에 저장된 뒤 k6가 그 경로에서 읽습니다. 실행 호스트와 업로드 경로가 같아야 합니다.
                  </UiAlert>
                  <input
                    :id="'scenario-multipart-file-' + si"
                    type="file"
                    class="scenario-multipart-file-input"
                    @change="onScenarioMultipartFile(si, $event)"
                  />
                  <div class="vf-row vf-row--dense align-center flex-wrap mb-2 ga-2">
                    <UiBtn type="button" variant="outlined" @click="openScenarioMultipartPicker(si)">
                      파일 업로드
                    </UiBtn>
                    <UiProgress v-if="step.multipartUploading" indeterminate class="flex-grow-1" style="max-width: 120px" />
                    <span v-if="step.multipartFileLabel" class="text-body-2 text-medium-emphasis multipart-file-name">
                      {{ step.multipartFileLabel }}
                    </span>
                  </div>
                  <UiAlert v-if="step.multipartUploadError" type="error" class="mb-2">{{ step.multipartUploadError }}</UiAlert>
                  <UiAlert
                    v-if="errors.scenarioMultipart && errors.scenarioMultipart[si]"
                    type="error"
                    class="mb-2"
                  >
                    {{ errors.scenarioMultipart[si] }}
                  </UiAlert>
                  <div class="vf-row vf-row--dense mb-2">
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.multipartFileField"
                        label="파일 파트 필드명"
                        placeholder="file"
                        hint="multipart에서 바이너리가 붙는 name 속성"
                        hide-details="auto"
                      />
                    </div>
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.multipartFilename"
                        label="서버에 전달되는 파일명 (선택)"
                        :placeholder="'예: upload-' + vuPlaceholder + '.bin'"
                        :hint="
                          'VU마다 다른 이름으로 보내려면 ' +
                          vuPlaceholder +
                          ' 를 넣으세요. 바이너리는 위에서 업로드한 파일과 동일합니다.'
                        "
                        hide-details="auto"
                        class="multipart-filename-field"
                      >
                        <template #append>
                          <UiBtn
                            type="button"
                            variant="outlined"
                            class="multipart-filename-vu-btn"
                            :title="vuPlaceholder + ' 를 파일명에 넣습니다'"
                            @click="appendVuToMultipartFilename(si)"
                          >
                            {{ vuPlaceholder }} 넣기
                          </UiBtn>
                        </template>
                      </UiTextField>
                    </div>
                  </div>
                  <UiTextField
                    v-model="step.multipartContentType"
                    label="파일 파트 Content-Type (선택)"
                    placeholder="비우면 octet-stream 또는 추정값"
                    class="mb-2"
                    hide-details="auto"
                  />
                  <p class="text-body-2 text-medium-emphasis mb-1">추가 텍스트 필드</p>
                  <div class="kv-section">
                    <div
                      v-for="(mf, fi) in step.multipartFieldsList"
                      :key="'mpf-' + si + '-' + fi"
                      class="kv-row"
                    >
                      <UiCheckbox v-model="mf.enabled" class="param-check flex-shrink-0" />
                      <UiTextField v-model="mf.key" placeholder="필드 이름" hide-details class="kv-key" />
                      <UiTextField
                        v-model="mf.value"
                        :placeholder="'값 (' + vuPlaceholder + ' 가능)'"
                        hide-details
                        class="kv-value"
                      />
                      <UiBtn
                        icon
                        variant="text"
                        color="error"
                        :disabled="step.multipartFieldsList.length <= 1"
                        @click="removeScenarioMultipartField(si, fi)"
                      >
                        <UiIcon icon="mdi-delete-outline" size="small" />
                      </UiBtn>
                    </div>
                    <UiBtn variant="outlined" class="mt-1" @click="addScenarioMultipartField(si)">필드 추가</UiBtn>
                  </div>
                </div>
              </div>
              <div v-show="step.scenarioTab === 'poll'">
                <UiAlert type="info" class="mb-3 poll-tab-help">
                  <div class="text-body-2">
                    이 단계는 <strong>같은 요청</strong>을 일정 간격으로 다시 보냅니다. 아래 중
                    <strong>하나라도</strong> 맞으면 이 단계는 성공으로 끝납니다.
                  </div>
                  <ul class="text-body-2 poll-tab-help__list mt-2 mb-0 pl-4">
                    <li>응답 <strong>상태 코드</strong>가 아래 목록에 포함될 때</li>
                    <li>응답이 <strong>2xx</strong>이고, JSON에서 고른 필드 값이 <strong>기대 문자열</strong>과 같을 때</li>
                  </ul>
                  <div class="text-body-2 mt-2">
                    <strong>진행 중(재시도)</strong>를 쓰면 2xx JSON이 그 값일 때만 다음 시도로 넘어갑니다. 성공 조건과 맞지 않으면 폴링을 바로 실패로 끝냅니다. 비2xx는 이 조건 없이 최대 시간까지 재시도합니다.
                  </div>
                  <div class="text-body-2 mt-2">
                    캡처(캡처 탭)는 <strong>성공으로 끝난 마지막 응답</strong>에만 적용됩니다.
                  </div>
                </UiAlert>
                <UiCheckbox v-model="step.pollEnabled" label="이 단계 폴링 사용" class="mb-2" />
                <template v-if="step.pollEnabled">
                  <UiAlert
                    v-if="errors.scenarioPoll && errors.scenarioPoll[si]"
                    type="error"
                    class="mb-2"
                  >
                    {{ errors.scenarioPoll[si] }}
                  </UiAlert>
                  <div class="vf-row vf-row--dense mb-2">
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollIntervalSeconds"
                        label="시도 간격(초)"
                        type="number"
                        min="0.1"
                        max="60"
                        step="0.1"
                        hide-details="auto"
                        hint="0.1~60"
                      />
                    </div>
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollMaxDurationSeconds"
                        label="최대 대기(초)"
                        type="number"
                        min="0.5"
                        max="600"
                        step="0.5"
                        hide-details="auto"
                        hint="첫 시도 시각 기준, 0.5~600"
                      />
                    </div>
                  </div>
                  <p class="text-body-2 text-medium-emphasis mb-1">성공 종료 조건</p>
                  <div class="vf-row vf-row--dense mb-2">
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollUntilJsonPath"
                        label="JSON 필드 경로 (선택)"
                        placeholder="예: status, data.ready"
                        hint="비우면 JSON으로는 성공 여부를 보지 않습니다. 점(.)으로 하위 필드를 적습니다."
                        hide-details="auto"
                      />
                    </div>
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollUntilEquals"
                        label="기대 문자열 (성공)"
                        placeholder="예: done, true"
                        :hint="
                          '성공 시 JSON 경로 값과 문자열 비교. ' +
                          vuPlaceholder +
                          '·캡처 변수 치환 가능.'
                        "
                        hide-details="auto"
                      />
                    </div>
                  </div>
                  <p class="text-body-2 text-medium-emphasis mb-1">진행 중(재시도, 선택)</p>
                  <div class="vf-row vf-row--dense mb-2">
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollWhileJsonPath"
                        label="JSON 필드 경로"
                        placeholder="예: status"
                        hint="비우면 생략. 2xx일 때 이 값이 아래와 같을 때만 간격 후 재시도."
                        hide-details="auto"
                      />
                    </div>
                    <div class="vf-col vf-col-12 vf-col-sm-6">
                      <UiTextField
                        v-model="step.pollWhileEquals"
                        label="기대 문자열 (진행 중)"
                        placeholder="예: running, pending"
                        :hint="'성공이 아닐 때 재시도 허용 조건. ' + vuPlaceholder + '·캡처 변수 치환 가능.'"
                        hide-details="auto"
                      />
                    </div>
                  </div>
                  <UiTextField
                    v-model="step.pollUntilStatusIn"
                    label="HTTP 상태 코드 (선택)"
                    placeholder="예: 200, 202"
                    hint="쉼표·공백·세미콜론으로 여러 개 입력. 비우면 상태만으로는 성공을 판단하지 않습니다."
                    hide-details="auto"
                  />
                </template>
              </div>
              <div v-show="step.scenarioTab === 'capture'">
                <UiAlert type="info" class="mb-3 capture-tab-help">
                  <div class="text-body-2">
                    HTTP <strong>2xx</strong>일 때만 값을 꺼냅니다.
                    <strong>JSON 본문</strong>: 응답을 JSON으로 파싱한 뒤 점(.) 경로로 필드를 고릅니다.
                    <strong>응답 헤더</strong>: 헤더 이름(key)으로 조회합니다(대소문자 무시). Set-Cookie는
                    <strong>쿠키 이름(선택)</strong>을 넣으면 <code class="capture-code">access_token=…; Path=/</code>에서 값(… )만 잘라 씁니다.
                    그다음 단계 URL·Params·Headers·Body에
                    <code v-pre class="capture-code">{{변수명}}</code>을 넣으면 치환됩니다. 변수명·JSON 경로·헤더 이름을 모두 비우면 캡처하지 않습니다.
                  </div>
                </UiAlert>
                <div class="vf-row vf-row--dense mb-2">
                  <div class="vf-col vf-col-12 vf-col-sm-6">
                    <UiSelect
                      v-model="step.captureFrom"
                      :items="captureSourceItems"
                      item-title="title"
                      item-value="value"
                      label="캡처 출처"
                      hide-details
                    />
                  </div>
                  <div class="vf-col vf-col-12 vf-col-sm-6">
                    <UiTextField
                      v-model="step.captureVar"
                      label="변수명"
                      placeholder="token"
                      hint="영문·숫자·밑줄. 다음 단계에 {{ 이름 }} 형태로 사용."
                      hide-details="auto"
                    />
                  </div>
                </div>
                <div class="vf-row vf-row--dense">
                  <div class="vf-col vf-col-12 vf-col-sm-6">
                    <UiTextField
                      v-if="step.captureFrom !== 'header'"
                      v-model="step.capturePath"
                      label="JSON 경로 (path)"
                      placeholder="예: access_token, data.id"
                      hint="응답 JSON 루트부터의 키 경로. 배열 인덱스(n)는 미지원."
                      hide-details="auto"
                    />
                    <UiTextField
                      v-else
                      v-model="step.captureHeader"
                      label="응답 헤더 이름"
                      placeholder="예: X-Request-Id, Set-Cookie"
                      hint="실제 응답 헤더 키와 대소문자만 다르면 같은 것으로 봅니다."
                      hide-details="auto"
                    />
                  </div>
                  <div v-if="step.captureFrom === 'header'" class="vf-col vf-col-12 vf-col-sm-6">
                    <UiTextField
                      v-model="step.captureCookieName"
                      label="쿠키 이름 (선택)"
                      placeholder="예: access_token"
                      hint="Set-Cookie 한 줄에서 이 이름의 값만 사용. 비우면 헤더 값 전체를 변수에 넣습니다."
                      hide-details="auto"
                    />
                  </div>
                </div>
              </div>
              <div v-show="step.scenarioTab === 'error'">
                <UiAlert type="info" class="mb-2">
                  판별 문자열을 모두 비우면 이 단계는 폼 아래 <strong>테스트 전역</strong> 에러 규칙을 씁니다. 한 줄이라도 채우면 이 단계만 아래 조건으로 검사합니다.
                </UiAlert>
                <div
                  v-for="(erow, eidx) in step.errorPageRules"
                  :key="'s' + si + '-err-' + eidx"
                  class="vf-row vf-row--dense align-end form-row-nowrap-sm error-page-row"
                >
                  <div class="vf-col vf-col-12 vf-col-sm-5 vf-col-md-4 flex-shrink-0 error-page-mode-col">
                    <UiSelect
                      v-model="erow.matchMode"
                      label="판별 방식"
                      :items="errorMatchModeItems"
                      item-title="title"
                      item-value="value"
                      hide-details
                    />
                  </div>
                  <div class="vf-col vf-col-12 vf-col-sm-6 vf-col-md-7 error-page-pattern-col">
                    <UiTextField
                      v-model="erow.pattern"
                      label="판별 문자열"
                      placeholder="비우면 이 줄 무시 · 전부 비우면 전역 규칙"
                      hide-details
                    />
                  </div>
                  <div class="vf-col vf-col-12 vf-col-sm-1 vf-col-md-1 d-flex align-center error-page-actions-col">
                    <UiBtn
                      v-if="step.errorPageRules.length > 1"
                      icon
                      variant="text"
                      aria-label="조건 삭제"
                      @click="removeScenarioErrorRule(si, eidx)"
                    >
                      <UiIcon icon="mdi-delete-outline" size="small" />
                    </UiBtn>
                    <UiBtn
                      v-if="eidx === step.errorPageRules.length - 1"
                      icon
                      variant="text"
                      aria-label="조건 추가"
                      @click="addScenarioErrorRule(si)"
                    >
                      <UiIcon icon="mdi-plus" size="small" />
                    </UiBtn>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <UiBtn variant="outlined" @click="addScenarioStep">단계 추가</UiBtn>
        </div>
      </div>
      <template v-if="form.engine !== 'http'">
        <br />
        <div class="ui-tabs request-tabs mb-2" role="tablist">
          <button
            type="button"
            class="ui-tabs__btn"
            :class="{ 'ui-tabs__btn--active': requestTab === 'params' }"
            @click="requestTab = 'params'"
          >
            Params
            <UiTooltip text="URL 뒤에 붙는 검색 조건(쿼리)입니다. (예: ?page=1)">
              <UiIcon icon="mdi-information-outline" size="14" class="ml-1 label-tip-icon" />
            </UiTooltip>
          </button>
          <button
            type="button"
            class="ui-tabs__btn"
            :class="{ 'ui-tabs__btn--active': requestTab === 'headers' }"
            @click="requestTab = 'headers'"
          >
            Headers
            <UiTooltip text="요청에 넣는 부가 정보입니다. (인증 토큰, Content-Type 등)">
              <UiIcon icon="mdi-information-outline" size="14" class="ml-1 label-tip-icon" />
            </UiTooltip>
          </button>
          <button
            type="button"
            class="ui-tabs__btn"
            :class="{ 'ui-tabs__btn--active': requestTab === 'body' }"
            @click="requestTab = 'body'"
          >
            Body
            <UiTooltip text="POST/PUT 등으로 보낼 본문 내용(JSON 등)입니다.">
              <UiIcon icon="mdi-information-outline" size="14" class="ml-1 label-tip-icon" />
            </UiTooltip>
          </button>
        </div>
        <div class="request-window">
          <div v-show="requestTab === 'params'">
            <div class="kv-section">
              <div v-for="(row, i) in form.paramsList" :key="i" class="kv-row">
                <UiCheckbox
                  v-model="row.enabled"
                  class="param-check flex-shrink-0"
                  @update:model-value="syncUrlFromParams"
                />
                <UiTextField
                  v-model="row.key"
                  placeholder="Key"
                  hide-details
                  class="kv-key"
                  @update:model-value="syncUrlFromParams"
                />
                <UiTextField
                  v-model="row.value"
                  :placeholder="'Value (VU별: value-' + vuPlaceholder + ')'"
                  hide-details
                  class="kv-value"
                  @update:model-value="syncUrlFromParams"
                />
                <UiBtn icon variant="text" color="error" :disabled="form.paramsList.length <= 1" @click="removeParam(i)">
                  <UiIcon icon="mdi-delete-outline" size="small" />
                </UiBtn>
              </div>
              <UiBtn variant="outlined" class="mt-1" @click="addParam">추가</UiBtn>
            </div>
          </div>
          <div v-show="requestTab === 'headers'">
            <div class="kv-section">
              <div v-for="(row, i) in form.headersList" :key="i" class="kv-row">
                <UiCheckbox v-model="row.enabled" class="param-check flex-shrink-0" />
                <UiTextField v-model="row.key" placeholder="Key" hide-details class="kv-key" />
                <UiTextField
                  v-model="row.value"
                  :placeholder="'Value (VU별: value-' + vuPlaceholder + ')'"
                  hide-details
                  class="kv-value"
                />
                <UiBtn icon variant="text" color="error" :disabled="form.headersList.length <= 1" @click="removeHeader(i)">
                  <UiIcon icon="mdi-delete-outline" size="small" />
                </UiBtn>
              </div>
              <UiBtn variant="outlined" class="mt-1" @click="addHeader">추가</UiBtn>
            </div>
          </div>
          <div v-show="requestTab === 'body'">
            <div class="textarea-col">
              <UiTextarea
                v-model="form.requestBody"
                :placeholder="'요청 본문 입력. VU마다 다르게 하려면 본문에 ' + vuPlaceholder + ' 를 넣으세요.'"
                rows="4"
                hide-details
              />
            </div>
          </div>
        </div>
      </template>

      <div v-if="form.engine === 'browser'" class="mt-3 browser-actions-section">
        <p class="text-subtitle-2 mb-2">로드 후 동작</p>
        <UiAlert type="info" class="mb-2 scenario-flow-hint">
          첫 페이지 로드 이후 순서대로 실행됩니다. k6 HTTP 다단계와는 별개입니다 (wait_selector · click · sleep).
        </UiAlert>
        <p class="text-caption text-medium-emphasis mb-2">
          새로 만들거나 저장된 동작이 없으면 «클릭» 한 줄(타임아웃 {{ browserActionDefaultTimeoutMs }}ms)이 들어갑니다. 선택자를 비운 채 저장하면 해당 줄은 보내지 않습니다.
        </p>
        <div
          v-for="(act, bi) in form.browserActions"
          :key="act.rowKey"
          class="mb-2 pa-2 browser-action-card"
        >
          <div class="vf-row vf-row--dense align-end">
            <div class="vf-col vf-col-12 vf-col-sm-5 vf-col-md-4">
              <UiSelect
                v-model="act.type"
                label="동작 유형"
                :items="browserActionTypeItems"
                item-title="title"
                item-value="value"
                hide-details
              />
            </div>
            <div class="vf-col vf-col-12 vf-col-sm-7 vf-col-md-8 d-flex align-center justify-end gap-0 flex-wrap">
              <UiBtn
                icon
                variant="text"
                aria-label="위로 이동"
                :disabled="bi === 0"
                @click="moveBrowserActionUp(bi)"
              >
                <UiIcon icon="mdi-arrow-up" size="small" />
              </UiBtn>
              <UiBtn
                icon
                variant="text"
                aria-label="아래로 이동"
                :disabled="bi >= form.browserActions.length - 1"
                @click="moveBrowserActionDown(bi)"
              >
                <UiIcon icon="mdi-arrow-down" size="small" />
              </UiBtn>
              <UiBtn
                icon
                variant="text"
                color="error"
                aria-label="동작 삭제"
                @click="removeBrowserAction(bi)"
              >
                <UiIcon icon="mdi-delete-outline" size="small" />
              </UiBtn>
            </div>
          </div>
          <div v-if="act.type !== 'sleep'" class="vf-row vf-row--dense mt-1">
            <div class="vf-col vf-col-12">
              <UiTextField
                v-model="act.selector"
                label="CSS 선택자"
                placeholder="#app button.primary"
                hide-details
              />
            </div>
          </div>
          <div v-if="act.type !== 'sleep'" class="vf-row vf-row--dense mt-1">
            <div class="vf-col vf-col-12 vf-col-sm-6 vf-col-md-4">
              <UiTextField
                v-model="act.timeoutMs"
                label="대기 타임아웃 (ms)"
                type="number"
                min="1000"
                max="60000"
                hide-details
              />
            </div>
          </div>
          <div v-else class="vf-row vf-row--dense mt-1">
            <div class="vf-col vf-col-12 vf-col-sm-6 vf-col-md-4">
              <UiTextField
                v-model="act.sleepMs"
                label="대기 시간 (ms)"
                type="number"
                min="0"
                max="30000"
                hide-details
              />
            </div>
          </div>
          <p v-if="errors.browserActions && errors.browserActions[bi]" class="field-error mt-1 mb-0">
            {{ errors.browserActions[bi] }}
          </p>
        </div>
        <UiBtn variant="outlined" class="mt-1" @click="addBrowserAction">동작 추가</UiBtn>
      </div>

      <div class="vf-row vf-row--dense load-settings-row mt-3">
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.vus"
              type="number"
              min="1"
              hide-details="auto"
              :error-messages="errors.vus ? [errors.vus] : []"
              label="VUs"
              class="flex-grow-1"
            />
            <UiTooltip text="동시에 요청을 보내는 '가상 사용자' 수입니다. 10이면 10명이 동시에 접속한 것처럼 테스트합니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.vuStart"
              type="number"
              min="1"
              hide-details="auto"
              :error-messages="errors.vuStart ? [errors.vuStart] : []"
              :label="vuPlaceholder + ' 시작 번호'"
              class="flex-grow-1"
            />
            <UiTooltip
              :text="'k6에서 첫 번째 VU(__VU=1)에 URL·본문 등의 ' + vuPlaceholder + ' 자리에 들어갈 숫자입니다. 이후 VU는 1씩 증가합니다.'"
            >
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.duration"
              type="number"
              min="1"
              hide-details="auto"
              :error-messages="errors.duration ? [errors.duration] : []"
              label="제한 시간(초)"
              class="flex-grow-1"
            />
            <UiTooltip text="테스트가 실행될 수 있는 최대 시간(초)입니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.requestDelay"
              type="number"
              min="0"
              step="0.1"
              hide-details
              label="대기(초)"
              class="flex-grow-1"
            />
            <UiTooltip text="한 번 요청을 보낸 뒤, 다음 요청 전에 기다리는 시간(초)입니다. 0이면 쉬지 않고 연속 요청합니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.rampUp"
              type="number"
              min="0"
              hide-details
              label="Ramp-up(초)"
              class="flex-grow-1"
            />
            <UiTooltip text="테스트 시작 시 가상 사용자를 0에서 설정한 수까지 서서히 늘리는 시간입니다. 서버에 부담을 줄일 수 있습니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.iterations"
              type="number"
              min="1"
              placeholder="비우면 제한 시간만큼"
              hide-details="auto"
              :error-messages="errors.iterations ? [errors.iterations] : []"
              label="반복 횟수 (선택)"
              class="flex-grow-1"
            />
            <UiTooltip text="각 가상 사용자가 요청을 보낼 횟수입니다. 비워두면 제한 시간(초) 동안만 반복합니다. 입력 시 1 이상의 정수.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
        <div class="vf-col vf-col-6 vf-col-sm-4 vf-col-md-2">
          <div class="d-flex align-start gap-1">
            <UiTextField
              v-model.number="form.bodyPreviewSize"
              type="number"
              min="0"
              max="10000"
              hide-details
              label="결과 화면 본문 표시(자)"
              class="flex-grow-1"
            />
            <UiTooltip text="실행 결과 목록·호버에서 응답 본문을 잘라 보여줄 글자 수입니다. DB에는 응답 본문 전체가 저장됩니다. 0이면 목록에는 …만 보이고 호버로 전체를 볼 수 있습니다.">
              <UiIcon icon="mdi-information-outline" size="small" class="label-tip-icon" />
            </UiTooltip>
          </div>
        </div>
      </div>
      <div class="mt-2 error-page-section">
        <div class="text-caption text-medium-emphasis mb-1">
          에러 페이지 판별 (URL·응답 본문). 조건을 여러 개 두면 <strong>하나라도</strong> 실패 조건이면 해당 요청이 실패로 집계됩니다.
        </div>
        <div
          v-for="(row, idx) in form.errorPageRules"
          :key="'err-' + idx"
          class="vf-row vf-row--dense align-end form-row-nowrap-sm error-page-row"
        >
          <div class="vf-col vf-col-12 vf-col-sm-5 vf-col-md-4 flex-shrink-0 error-page-mode-col">
            <UiSelect
              v-model="row.matchMode"
              label="판별 방식"
              :items="errorMatchModeItems"
              item-title="title"
              item-value="value"
              hide-details
            />
          </div>
          <div class="vf-col vf-col-12 vf-col-sm-6 vf-col-md-7 error-page-pattern-col">
            <UiTextField
              v-model="row.pattern"
              label="판별 문자열"
              placeholder="비우면 이 줄은 무시"
              hide-details
            />
          </div>
          <div class="vf-col vf-col-12 vf-col-sm-1 vf-col-md-1 d-flex align-center error-page-actions-col">
            <UiBtn
              v-if="form.errorPageRules.length > 1"
              icon
              variant="text"
              aria-label="조건 삭제"
              @click="removeErrorPageRule(idx)"
            >
              <UiIcon icon="mdi-delete-outline" size="small" />
            </UiBtn>
            <UiBtn
              v-if="idx === form.errorPageRules.length - 1"
              icon
              variant="text"
              aria-label="조건 추가"
              @click="addErrorPageRule"
            >
              <UiIcon icon="mdi-plus" size="small" />
            </UiBtn>
          </div>
        </div>
      </div>
      <div class="d-flex align-center flex-wrap mt-2">
        <UiBtn native-type="submit" color="primary" variant="flat" :loading="saving" class="mr-2">저장</UiBtn>
        <UiBtn v-if="isEdit" :to="`/tests/${testId}/run`" variant="text" color="primary" class="mr-2">실행</UiBtn>
        <UiBtn to="/tests" variant="text">목록으로</UiBtn>
      </div>
      <UiAlert v-if="apiError" type="error" class="mt-2">{{ apiError }}</UiAlert>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post, put, getApiErrorMessage, postK6Fixture } from '../services/api'
import { normalizeTagList, tagColorKey } from '../utils/tags'
import UiProgress from '../components/UiProgress.vue'
import UiAlert from '../components/UiAlert.vue'
import UiBtn from '../components/UiBtn.vue'
import UiTextField from '../components/UiTextField.vue'
import UiTextarea from '../components/UiTextarea.vue'
import UiSelect from '../components/UiSelect.vue'
import UiCheckbox from '../components/UiCheckbox.vue'
import UiChip from '../components/UiChip.vue'
import UiIcon from '../components/UiIcon.vue'
import UiTooltip from '../components/UiTooltip.vue'

const vuPlaceholder = '{{VU}}'
/** 로드 후 동작 기본 타임아웃(ms) — 빈 폼 첫 행에 사용 */
const browserActionDefaultTimeoutMs = 3000

function nextBrowserActionRowKey() {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `ba-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}
const errorMatchModeItems = [
  { title: '판별 문구가 있으면 실패', value: 'contains' },
  { title: '판별 문구가 없으면 실패', value: 'not_contains' },
]
const captureSourceItems = [
  { title: 'JSON 본문 (path)', value: 'json' },
  { title: '응답 헤더', value: 'header' },
]
const browserActionTypeItems = [
  { title: '요소 나타날 때까지 대기 (wait_selector)', value: 'wait_selector' },
  { title: '클릭 (click)', value: 'click' },
  { title: '대기 (sleep)', value: 'sleep' },
]
const scenarioBodyKindItems = [
  { title: '텍스트 본문', value: 'raw' },
  { title: 'multipart (파일)', value: 'multipart' },
]
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'test-edit')
const testId = computed(() => (isEdit.value ? String(route.params.id) : ''))
const cloneFromId = computed(() => (route.query.cloneFrom ? String(route.query.cloneFrom) : ''))
const loading = ref(false)
const loadError = ref('')
const saving = ref(false)
const apiError = ref('')
const tagDraft = ref('')
const existingTagNames = ref([])
const tagPanelOpen = ref(false)
const tagHighlightIndex = ref(-1)
const errors = reactive({})
const requestTab = ref('params')
const urlDisplay = ref('')

/** API 응답에서 targetUrl이 빈 문자열이고 target_url에만 있을 때 ?? 로는 못 잡음 → || 사용 */
function pickTargetUrlFromApi(t) {
  if (!t || typeof t !== 'object') return ''
  return String(t.targetUrl || t.target_url || '').trim()
}

function onUrlDisplayInput(v) {
  urlDisplay.value = v != null ? String(v) : ''
}

/** load / loadForClone 겹침 시 늦게 도착한 응답이 폼을 덮어쓰지 않게 */
let remoteFormLoadGen = 0

function emptyScenarioStep() {
  return {
    name: '',
    method: 'GET',
    url: '',
    scenarioTab: 'params',
    paramsList: [{ key: '', value: '', enabled: false }],
    headersList: [{ key: '', value: '', enabled: false }],
    bodyKind: 'raw',
    body: '',
    multipartFilePath: '',
    multipartFileLabel: '',
    multipartFileField: 'file',
    multipartFilename: '',
    multipartContentType: '',
    multipartFieldsList: [{ key: '', value: '', enabled: false }],
    multipartUploading: false,
    multipartUploadError: '',
    captureFrom: 'json',
    capturePath: '',
    captureHeader: '',
    captureCookieName: '',
    captureVar: '',
    sleepAfterSeconds: '',
    pollEnabled: false,
    pollIntervalSeconds: '1',
    pollMaxDurationSeconds: '30',
    pollUntilJsonPath: '',
    pollUntilEquals: '',
    pollUntilStatusIn: '',
    pollWhileJsonPath: '',
    pollWhileEquals: '',
    errorPageRules: [{ pattern: '', matchMode: 'contains' }],
  }
}

const scenarioSteps = ref([emptyScenarioStep()])

function addScenarioStep() {
  scenarioSteps.value.push(emptyScenarioStep())
}

function removeScenarioStep(i) {
  if (scenarioSteps.value.length <= 1) return
  scenarioSteps.value.splice(i, 1)
}

function addScenarioErrorRule(stepIndex) {
  scenarioSteps.value[stepIndex].errorPageRules.push({ pattern: '', matchMode: 'contains' })
}

function removeScenarioErrorRule(stepIndex, idx) {
  const list = scenarioSteps.value[stepIndex].errorPageRules
  if (list.length <= 1) return
  list.splice(idx, 1)
}

function addScenarioHeader(stepIndex) {
  scenarioSteps.value[stepIndex].headersList.push({ key: '', value: '', enabled: false })
}

function removeScenarioHeader(stepIndex, hi) {
  const list = scenarioSteps.value[stepIndex].headersList
  if (list.length <= 1) return
  list.splice(hi, 1)
}

function addScenarioParam(stepIndex) {
  scenarioSteps.value[stepIndex].paramsList.push({ key: '', value: '', enabled: false })
}

function removeScenarioParam(stepIndex, pi) {
  const list = scenarioSteps.value[stepIndex].paramsList
  if (list.length <= 1) return
  list.splice(pi, 1)
}

function addScenarioMultipartField(stepIndex) {
  scenarioSteps.value[stepIndex].multipartFieldsList.push({ key: '', value: '', enabled: false })
}

function removeScenarioMultipartField(stepIndex, fi) {
  const list = scenarioSteps.value[stepIndex].multipartFieldsList
  if (list.length <= 1) return
  list.splice(fi, 1)
}

function onScenarioBodyKindChange(step, kind) {
  if (kind === 'raw') {
    step.multipartFilePath = ''
    step.multipartFileLabel = ''
    step.multipartFileField = 'file'
    step.multipartFilename = ''
    step.multipartContentType = ''
    step.multipartFieldsList = [{ key: '', value: '', enabled: false }]
    step.multipartUploadError = ''
  } else {
    step.body = ''
  }
}

function openScenarioMultipartPicker(stepIndex) {
  const el = document.getElementById(`scenario-multipart-file-${stepIndex}`)
  el?.click()
}

function appendVuToMultipartFilename(stepIndex) {
  const step = scenarioSteps.value[stepIndex]
  const ph = vuPlaceholder
  let cur = step.multipartFilename != null ? String(step.multipartFilename) : ''
  if (cur.includes(ph)) return
  if (!cur.trim()) {
    step.multipartFilename = `upload-${ph}.bin`
    return
  }
  const endsOk = cur.endsWith('_') || cur.endsWith('-') || cur.endsWith('.')
  step.multipartFilename = endsOk ? `${cur}${ph}` : `${cur}_${ph}`
}

async function onScenarioMultipartFile(stepIndex, event) {
  const input = event.target
  const file = input?.files?.[0]
  if (!file || !input) return
  const step = scenarioSteps.value[stepIndex]
  step.multipartUploading = true
  step.multipartUploadError = ''
  try {
    const r = await postK6Fixture(file)
    step.multipartFilePath = r.filePath || ''
    step.multipartFileLabel = r.fileName || file.name
    const ct = (r.contentType || '').trim()
    if (ct && !(step.multipartContentType || '').trim()) {
      step.multipartContentType = ct
    }
  } catch (err) {
    step.multipartUploadError = getApiErrorMessage(err)
    step.multipartFilePath = ''
    step.multipartFileLabel = ''
  } finally {
    step.multipartUploading = false
    input.value = ''
  }
}

function stepFromApi(s) {
  const headers = s.headers && typeof s.headers === 'object' ? s.headers : {}
  const hEntries = Object.entries(headers)
  const qp = Array.isArray(s.queryParams) ? s.queryParams : []
  const paramsList = qp.length
    ? qp.map((item) => ({
        key: item && typeof item === 'object' && 'key' in item ? String(item.key ?? '') : '',
        value: item && typeof item === 'object' && 'value' in item ? String(item.value ?? '') : '',
        enabled: true,
      }))
    : [{ key: '', value: '', enabled: false }]
  const mp = s.multipart && typeof s.multipart === 'object' ? s.multipart : null
  const mpPath = mp ? String(mp.filePath || mp.file_path || '').trim() : ''
  const bodyKind = mpPath ? 'multipart' : 'raw'
  const rawFields = mp?.fields && typeof mp.fields === 'object' && !Array.isArray(mp.fields) ? mp.fields : {}
  const multipartFieldsList = Object.keys(rawFields).length
    ? Object.entries(rawFields).map(([k, v]) => ({
        key: k,
        value: String(v ?? ''),
        enabled: true,
      }))
    : [{ key: '', value: '', enabled: false }]
  const mpField = mp ? String(mp.fileField || mp.file_field || '').trim() : ''
  const mpFilename = mp?.filename != null ? String(mp.filename) : ''
  const mpCt = mp?.contentType != null ? String(mp.contentType) : ''
  const pPol = s.poll && typeof s.poll === 'object' ? s.poll : null
  const iv0 = pPol != null ? (pPol.intervalSeconds ?? pPol.interval_seconds) : null
  const md0 = pPol != null ? (pPol.maxDurationSeconds ?? pPol.max_duration_seconds) : null
  const pollEnabled = pPol != null && iv0 != null && md0 != null
  const usi = pPol && Array.isArray(pPol.untilStatusIn || pPol.until_status_in)
    ? pPol.untilStatusIn || pPol.until_status_in
    : []
  return {
    name: s.name || '',
    method: s.method || 'GET',
    url: s.url || '',
    scenarioTab: 'params',
    paramsList,
    headersList: hEntries.length
      ? hEntries.map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
      : [{ key: '', value: '', enabled: false }],
    bodyKind,
    body: bodyKind === 'raw' ? (s.body || '') : '',
    multipartFilePath: mpPath,
    multipartFileLabel: mpPath ? mpFilename || mpPath.split(/[/\\]/).pop() || '서버 파일' : '',
    multipartFileField: mpField || 'file',
    multipartFilename: bodyKind === 'multipart' ? mpFilename : '',
    multipartContentType: bodyKind === 'multipart' ? mpCt : '',
    multipartFieldsList,
    multipartUploading: false,
    multipartUploadError: '',
    captureFrom: s.capture && String(s.capture.from || '').toLowerCase() === 'header' ? 'header' : 'json',
    capturePath: s.capture?.path || '',
    captureHeader: s.capture?.header || '',
    captureCookieName: s.capture?.cookieName || '',
    captureVar: s.capture?.var || '',
    sleepAfterSeconds:
      s.sleepAfterSeconds != null && s.sleepAfterSeconds !== '' ? String(s.sleepAfterSeconds) : '',
    pollEnabled,
    pollIntervalSeconds: pollEnabled ? String(iv0) : '1',
    pollMaxDurationSeconds: pollEnabled ? String(md0) : '30',
    pollUntilJsonPath:
      pPol && (pPol.untilJsonPath != null || pPol.until_json_path != null)
        ? String(pPol.untilJsonPath ?? pPol.until_json_path ?? '')
        : '',
    pollUntilEquals:
      pPol && (pPol.untilEquals !== undefined || pPol.until_equals !== undefined)
        ? String(pPol.untilEquals ?? pPol.until_equals ?? '')
        : '',
    pollUntilStatusIn: usi.length ? usi.join(', ') : '',
    pollWhileJsonPath:
      pPol && (pPol.whileJsonPath != null || pPol.while_json_path != null)
        ? String(pPol.whileJsonPath ?? pPol.while_json_path ?? '')
        : '',
    pollWhileEquals:
      pPol && (pPol.whileEquals !== undefined || pPol.while_equals !== undefined)
        ? String(pPol.whileEquals ?? pPol.while_equals ?? '')
        : '',
    errorPageRules: (() => {
      const er = s.errorPageRules ?? s.error_page_rules
      if (Array.isArray(er) && er.length) {
        return er.map((r) => ({
          pattern: r && r.pattern != null ? String(r.pattern) : '',
          matchMode:
            r && (r.matchMode === 'not_contains' || r.match_mode === 'not_contains')
              ? 'not_contains'
              : 'contains',
        }))
      }
      return [{ pattern: '', matchMode: 'contains' }]
    })(),
  }
}

/** 레거시 단일 URL 테스트(DB의 targetUrl·queryParams 등) → 편집용 1단계. */
function legacyHttpFieldsToScenarioStep(t) {
  let qp = []
  const qraw = t.queryParams ?? ''
  if (qraw && String(qraw).trim()) {
    try {
      const arr = JSON.parse(String(qraw))
      if (Array.isArray(arr)) qp = arr
    } catch {
      qp = []
    }
  }
  let headers = {}
  const hraw = t.headers ?? ''
  if (hraw && String(hraw).trim()) {
    try {
      const o = JSON.parse(String(hraw))
      if (o && typeof o === 'object' && !Array.isArray(o)) headers = o
    } catch {
      headers = {}
    }
  }
  return stepFromApi({
    method: t.httpMethod ?? 'GET',
    url: t.targetUrl ?? '',
    queryParams: qp,
    headers,
    body: t.requestBody ?? '',
  })
}

function scenarioStepFromCurrentBrowserForm() {
  return legacyHttpFieldsToScenarioStep({
    targetUrl: form.baseUrl,
    queryParams: buildQueryParamsJson() ?? '',
    httpMethod: form.httpMethod,
    requestBody: form.requestBody,
    headers: buildHeadersJson() ?? '',
  })
}

function parsePollStatusInInput(str) {
  if (!str || !String(str).trim()) return []
  return String(str)
    .split(/[,;\s]+/)
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => parseInt(x, 10))
    .filter((n) => Number.isFinite(n) && Number.isInteger(n))
}

function buildHttpScenarioPayload() {
  const out = []
  for (const s of scenarioSteps.value) {
    const u = (s.url || '').trim()
    if (!u) continue
    const capVar = (s.captureVar || '').trim()
    const row = {
      name: (s.name || '').trim() || undefined,
      method: s.method || 'GET',
      url: u,
    }
    const qp = (s.paramsList || [])
      .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
      .map((r) => ({ key: String(r.key).trim(), value: r.value != null ? String(r.value).trim() : '' }))
    if (qp.length) row.queryParams = qp
    const h = {}
    ;(s.headersList || [])
      .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
      .forEach((r) => {
        h[String(r.key).trim()] = r.value != null ? String(r.value).trim() : ''
      })
    if (Object.keys(h).length) row.headers = h
    if (s.bodyKind === 'multipart') {
      const fp = (s.multipartFilePath || '').trim()
      const ff = (s.multipartFileField || '').trim()
      if (fp && ff) {
        const mf = { filePath: fp, fileField: ff }
        const fn = (s.multipartFilename || '').trim()
        if (fn) mf.filename = fn
        const ct = (s.multipartContentType || '').trim()
        if (ct) mf.contentType = ct
        const fields = {}
        ;(s.multipartFieldsList || [])
          .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
          .forEach((r) => {
            fields[String(r.key).trim()] = r.value != null ? String(r.value).trim() : ''
          })
        if (Object.keys(fields).length) mf.fields = fields
        row.multipart = mf
      }
    } else {
      const b = (s.body || '').trim()
      if (b) row.body = b
    }
    if (capVar) {
      if (s.captureFrom === 'header') {
        const ch = (s.captureHeader || '').trim()
        if (ch) {
          const ccn = (s.captureCookieName || '').trim()
          row.capture = ccn
            ? { from: 'header', header: ch, cookieName: ccn, var: capVar }
            : { from: 'header', header: ch, var: capVar }
        }
      } else {
        const capPath = (s.capturePath || '').trim()
        if (capPath) row.capture = { from: 'json', path: capPath, var: capVar }
      }
    }
    const rawSleep = s.sleepAfterSeconds
    if (rawSleep != null && rawSleep !== '') {
      const n = Number(rawSleep)
      if (!Number.isNaN(n) && n > 0) row.sleepAfterSeconds = n
    }
    if (s.pollEnabled) {
      const iv = Number(s.pollIntervalSeconds)
      const md = Number(s.pollMaxDurationSeconds)
      const path = (s.pollUntilJsonPath || '').trim()
      const statuses = parsePollStatusInInput(s.pollUntilStatusIn)
      const pollObj = {
        intervalSeconds: iv,
        maxDurationSeconds: md,
      }
      if (path) {
        pollObj.untilJsonPath = path
        pollObj.untilEquals = s.pollUntilEquals != null ? String(s.pollUntilEquals) : ''
      }
      if (statuses.length) pollObj.untilStatusIn = statuses
      const wPath = (s.pollWhileJsonPath || '').trim()
      if (wPath) {
        pollObj.whileJsonPath = wPath
        pollObj.whileEquals = s.pollWhileEquals != null ? String(s.pollWhileEquals) : ''
      }
      row.poll = pollObj
    }
    const stepErrRules = (s.errorPageRules || [])
      .map((r) => ({
        pattern: (r.pattern || '').trim(),
        matchMode: r.matchMode === 'not_contains' ? 'not_contains' : 'contains',
      }))
      .filter((r) => r.pattern)
    if (stepErrRules.length) row.errorPageRules = stepErrRules
    out.push(row)
  }
  return out
}

const form = reactive({
  name: '',
  engine: 'http',
  baseUrl: '',
  paramsList: [{ key: '', value: '', enabled: false }],
  httpMethod: 'GET',
  requestBody: '',
  headersList: [{ key: '', value: '', enabled: false }],
  vus: 1,
  vuStart: 1,
  duration: 10,
  requestDelay: null,
  rampUp: 0,
  iterations: null,
  bodyPreviewSize: 500,
  vuUrlSuffix: false,
  errorPageRules: [{ pattern: '', matchMode: 'contains' }],
  tags: [],
  /** 브라우저 전용: 로드 후 Playwright 단계 (API browserActions) */
  browserActions: [],
  /** db 전용: xk6-sql 드라이버와 실행할 SQL. DSN은 baseUrl 재사용. */
  dbDriver: 'postgres',
  dbQuery: '',
})

const filteredSuggestions = computed(() => {
  const needle = (tagDraft.value || '').trim().toLowerCase()
  const pool = existingTagNames.value.filter((t) => !form.tags.includes(t))
  if (!needle) return pool.slice(0, 40)
  return pool.filter((t) => t.toLowerCase().includes(needle)).slice(0, 40)
})

watch(filteredSuggestions, (list) => {
  tagHighlightIndex.value = list.length ? 0 : -1
})

async function loadExistingTags() {
  try {
    const data = await get('tests/tags')
    existingTagNames.value = Array.isArray(data.items) ? data.items : []
  } catch {
    existingTagNames.value = []
  }
}

function onTagFocus() {
  tagPanelOpen.value = true
}

function onTagInputBlur() {
  window.setTimeout(() => {
    tagPanelOpen.value = false
  }, 180)
}

function onTagArrowDown() {
  const list = filteredSuggestions.value
  if (!list.length) return
  tagPanelOpen.value = true
  const n = list.length
  if (tagHighlightIndex.value < 0) tagHighlightIndex.value = 0
  else tagHighlightIndex.value = (tagHighlightIndex.value + 1) % n
}

function onTagArrowUp() {
  const list = filteredSuggestions.value
  if (!list.length) return
  tagPanelOpen.value = true
  const n = list.length
  if (tagHighlightIndex.value < 0) tagHighlightIndex.value = n - 1
  else tagHighlightIndex.value = (tagHighlightIndex.value - 1 + n) % n
}

function onTagEnter() {
  const list = filteredSuggestions.value
  if (
    tagPanelOpen.value
    && list.length > 0
    && tagHighlightIndex.value >= 0
    && tagHighlightIndex.value < list.length
  ) {
    selectSuggestion(list[tagHighlightIndex.value])
    return
  }
  addTagsFromDraft()
}

function selectSuggestion(name) {
  addTagNamed(name)
}

function addTagNamed(name) {
  const t = String(name || '').trim().slice(0, 32)
  if (!t || form.tags.includes(t)) return
  if (form.tags.length >= 32) return
  form.tags.push(t)
  tagDraft.value = ''
}

function addTagsFromDraft() {
  const raw = (tagDraft.value || '').trim()
  if (!raw) return
  const parts = raw.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
  const seen = new Set(form.tags.map((x) => String(x)))
  for (const p of parts) {
    const t = p.slice(0, 32)
    if (!t || seen.has(t)) continue
    if (form.tags.length >= 32) break
    seen.add(t)
    form.tags.push(t)
  }
  tagDraft.value = ''
}

function removeTag(i) {
  form.tags.splice(i, 1)
}

function buildEffectiveUrl() {
  const base = (form.baseUrl || '').trim()
  const pairs = form.paramsList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .map((r) => encodeURIComponent(String(r.key).trim()) + '=' + encodeURIComponent(r.value != null ? String(r.value).trim() : ''))
  return pairs.length ? base + (base.includes('?') ? '&' : '?') + pairs.join('&') : base
}

function parseUrlAndSyncToParams() {
  const s = (urlDisplay.value || '').trim()
  if (!s) {
    form.baseUrl = ''
    form.paramsList = [{ key: '', value: '', enabled: false }]
    return
  }
  const q = s.indexOf('?')
  const base = q >= 0 ? s.slice(0, q) : s
  form.baseUrl = base
  if (q >= 0 && q < s.length - 1) {
    const query = s.slice(q + 1)
    const list = []
    query.split('&').forEach((pair) => {
      const eq = pair.indexOf('=')
      const k = eq >= 0 ? decodeURIComponent(pair.slice(0, eq).replace(/\+/g, ' ')) : decodeURIComponent(pair.replace(/\+/g, ' '))
      const v = eq >= 0 ? decodeURIComponent(pair.slice(eq + 1).replace(/\+/g, ' ')) : ''
      if (k) list.push({ key: k, value: v, enabled: true })
    })
    form.paramsList = list.length ? list : [{ key: '', value: '', enabled: false }]
  } else {
    form.paramsList = [{ key: '', value: '', enabled: false }]
  }
  urlDisplay.value = buildEffectiveUrl()
}

function syncUrlFromParams() {
  urlDisplay.value = buildEffectiveUrl()
}

/** GET으로 불러온 테스트를 폼에 넣는 동안에는 엔진 전환 watch가 빈 시나리오로 덮어쓰지 않게 함 */
let applyingTestFromApi = false

watch(
  () => [form.baseUrl, form.paramsList],
  () => {
    if (applyingTestFromApi) return
    syncUrlFromParams()
  },
  { deep: true },
)

watch(
  () => form.engine,
  (e, prev) => {
    if (prev === undefined) return
    if (applyingTestFromApi) return
    if (e === 'browser' && prev === 'http') {
      const first = scenarioSteps.value[0]
      // 브라우저 테스트 불러오기 후에는 scenarioSteps가 빈 단계로만 채워져 있어,
      // 여기서 복사하면 API로 채운 baseUrl·params 등이 지워진다. 첫 단계 URL이 있을 때만 HTTP 단계 → 폼 동기화.
      if (first && (first.url || '').trim()) {
        form.httpMethod = first.method || 'GET'
        form.baseUrl = (first.url || '').trim()
        form.paramsList = JSON.parse(
          JSON.stringify(first.paramsList || [{ key: '', value: '', enabled: false }]),
        )
        form.headersList = JSON.parse(
          JSON.stringify(first.headersList || [{ key: '', value: '', enabled: false }]),
        )
        form.requestBody = first.bodyKind === 'raw' ? (first.body != null ? String(first.body) : '') : ''
        syncUrlFromParams()
      }
      if (!form.browserActions.length) {
        form.browserActions.push(emptyBrowserActionRow())
      }
    } else if (e === 'http' && prev === 'browser') {
      scenarioSteps.value = [scenarioStepFromCurrentBrowserForm()]
      form.browserActions = []
    }
  },
)

function addParam() {
  form.paramsList.push({ key: '', value: '', enabled: false })
}

function removeParam(i) {
  if (form.paramsList.length <= 1) return
  form.paramsList.splice(i, 1)
  syncUrlFromParams()
}

function addHeader() {
  form.headersList.push({ key: '', value: '', enabled: false })
}

function removeHeader(i) {
  if (form.headersList.length <= 1) return
  form.headersList.splice(i, 1)
}

function addErrorPageRule() {
  form.errorPageRules.push({ pattern: '', matchMode: 'contains' })
}

function removeErrorPageRule(i) {
  if (form.errorPageRules.length <= 1) return
  form.errorPageRules.splice(i, 1)
}

function buildQueryParamsJson() {
  const list = form.paramsList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .map((r) => ({ key: String(r.key).trim(), value: r.value != null ? String(r.value).trim() : '' }))
  return list.length ? JSON.stringify(list) : undefined
}

function buildHeadersJson() {
  const obj = {}
  form.headersList
    .filter((r) => r.enabled !== false && r.key != null && String(r.key).trim())
    .forEach((r) => {
      obj[String(r.key).trim()] = r.value != null ? String(r.value).trim() : ''
    })
  return Object.keys(obj).length ? JSON.stringify(obj) : undefined
}

function parseQueryParamsToList(raw) {
  if (Array.isArray(raw)) {
    const arr = raw
    if (!arr.length) return [{ key: '', value: '', enabled: false }]
    const list = arr.map((item) => {
      const k = item && typeof item === 'object' && 'key' in item ? String(item.key ?? '') : ''
      const v = item && typeof item === 'object' && 'value' in item ? String(item.value ?? '') : ''
      return { key: k, value: v, enabled: true }
    })
    return list.length ? list : [{ key: '', value: '', enabled: false }]
  }
  const str = raw
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: false }]
  try {
    const arr = JSON.parse(str)
    if (!Array.isArray(arr) || !arr.length) return [{ key: '', value: '', enabled: false }]
    const list = arr.map((item) => {
      const k = item && typeof item === 'object' && 'key' in item ? String(item.key ?? '') : ''
      const v = item && typeof item === 'object' && 'value' in item ? String(item.value ?? '') : ''
      return { key: k, value: v, enabled: true }
    })
    return list.length ? list : [{ key: '', value: '', enabled: false }]
  } catch {
    return [{ key: '', value: '', enabled: false }]
  }
}

function parseHeadersToList(raw) {
  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    const entries = Object.entries(raw).map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
    return entries.length ? entries : [{ key: '', value: '', enabled: false }]
  }
  const str = raw
  if (!str || !String(str).trim()) return [{ key: '', value: '', enabled: false }]
  try {
    const obj = JSON.parse(str)
    if (!obj || typeof obj !== 'object') return [{ key: '', value: '', enabled: false }]
    const entries = Object.entries(obj).map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
    return entries.length ? entries : [{ key: '', value: '', enabled: false }]
  } catch {
    return [{ key: '', value: '', enabled: false }]
  }
}

/** errorPageRules가 배열이 아니라 JSON 문자열로 올 때(직접 DB 조회 등) */
function parseErrorPageRulesFromPayload(raw) {
  if (raw == null) return null
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string' && raw.trim()) {
    try {
      const a = JSON.parse(raw)
      return Array.isArray(a) ? a : null
    } catch {
      return null
    }
  }
  return null
}

/** API가 camelCase 또는 snake_case로 올 때 모두 사용 */
function normalizeTestPayload(t) {
  if (!t || typeof t !== 'object') return t
  return {
    ...t,
    targetUrl: pickTargetUrlFromApi(t),
    queryParams: t.queryParams ?? t.query_params,
    httpMethod: t.httpMethod ?? t.http_method ?? 'GET',
    requestBody: t.requestBody ?? t.request_body,
    headers: t.headers,
    engine: t.engine,
    httpScenario: t.httpScenario ?? t.http_scenario,
    errorPageRules: t.errorPageRules ?? t.error_page_rules,
    errorPagePattern: t.errorPagePattern ?? t.error_page_pattern,
    errorPageMatchMode: t.errorPageMatchMode ?? t.error_page_match_mode,
    vuUrlSuffix: t.vuUrlSuffix ?? t.vu_url_suffix,
    vuStart: t.vuStart ?? t.vu_start,
    bodyPreviewSize: t.bodyPreviewSize ?? t.body_preview_size,
    requestDelay: t.requestDelay ?? t.request_delay,
    rampUp: t.rampUp ?? t.ramp_up,
    browserActions: t.browserActions ?? t.browser_actions,
    dbDriver: t.dbDriver ?? t.db_driver,
    dbQuery: t.dbQuery ?? t.db_query,
  }
}

function emptyBrowserActionRow() {
  return {
    rowKey: nextBrowserActionRowKey(),
    type: 'click',
    selector: '',
    timeoutMs: String(browserActionDefaultTimeoutMs),
    sleepMs: '',
  }
}

function browserActionRowFromApi(a) {
  if (!a || typeof a !== 'object') return emptyBrowserActionRow()
  const rawType = String(a.type ?? a.kind ?? 'click').trim()
  const type =
    rawType === 'wait_selector' || rawType === 'click' || rawType === 'sleep' ? rawType : 'click'
  const tms = a.timeoutMs ?? a.timeout_ms
  const sms = a.sleepMs ?? a.sleep_ms
  return {
    rowKey: nextBrowserActionRowKey(),
    type,
    selector: a.selector != null ? String(a.selector) : '',
    timeoutMs:
      tms != null && tms !== '' && !Number.isNaN(Number(tms)) ? String(Number(tms)) : '30000',
    sleepMs: sms != null && sms !== '' && !Number.isNaN(Number(sms)) ? String(Number(sms)) : '',
  }
}

function parseBrowserActionsFromPayload(raw) {
  if (raw == null) return []
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string' && raw.trim()) {
    try {
      const a = JSON.parse(raw)
      return Array.isArray(a) ? a : []
    } catch {
      return []
    }
  }
  return []
}

function addBrowserAction() {
  form.browserActions.push(emptyBrowserActionRow())
}

function removeBrowserAction(i) {
  form.browserActions.splice(i, 1)
}

function moveBrowserActionUp(i) {
  if (i <= 0) return
  const arr = form.browserActions
  const item = arr.splice(i, 1)[0]
  arr.splice(i - 1, 0, item)
}

function moveBrowserActionDown(i) {
  const arr = form.browserActions
  if (i >= arr.length - 1) return
  const item = arr.splice(i, 1)[0]
  arr.splice(i + 1, 0, item)
}

/** API 제출용: 빈 행 제거, 스키마에 맞게 숫자 보정 */
function buildBrowserActionsPayload() {
  const out = []
  for (const row of form.browserActions) {
    const kind = String(row.type || 'click').trim()
    if (kind !== 'wait_selector' && kind !== 'click' && kind !== 'sleep') continue
    const toRaw = Number(row.timeoutMs)
    const timeoutMs = Number.isFinite(toRaw)
      ? Math.min(60_000, Math.max(1_000, Math.round(toRaw)))
      : 30_000
    if (kind === 'sleep') {
      const smRaw = Number(row.sleepMs)
      if (!Number.isFinite(smRaw)) continue
      const sleepMs = Math.min(30_000, Math.max(0, Math.round(smRaw)))
      out.push({ type: 'sleep', sleepMs, timeoutMs: 30_000 })
    } else {
      const sel = String(row.selector ?? '').trim()
      if (!sel) continue
      out.push({ type: kind, selector: sel, timeoutMs })
    }
  }
  return out
}

function fillFormFromTest(t, clone = false) {
  applyingTestFromApi = true
  try {
    t = normalizeTestPayload(t)
    form.name = clone ? `복사 - ${t.name ?? ''}` : (t.name ?? '')
    form.engine = (t.engine === 'browser' || t.engine === 'db') ? t.engine : 'http'
    form.dbDriver = (t.dbDriver ?? 'postgres') || 'postgres'
    form.dbQuery = t.dbQuery ?? ''
    form.baseUrl = pickTargetUrlFromApi(t)
    form.paramsList = parseQueryParamsToList(t.queryParams ?? '')
    form.httpMethod = t.httpMethod ?? 'GET'
    form.requestBody = t.requestBody ?? ''
    form.headersList = parseHeadersToList(t.headers ?? '')
    const hs = t.httpScenario
    if (
      form.engine === 'browser'
      && !(form.baseUrl || '').trim()
      && Array.isArray(hs)
      && hs.length > 0
    ) {
      const step = stepFromApi(hs[0])
      form.baseUrl = (step.url || '').trim()
      form.paramsList = step.paramsList
      form.httpMethod = step.method || 'GET'
      form.headersList = step.headersList
      form.requestBody = step.bodyKind === 'raw' ? (step.body != null ? String(step.body) : '') : ''
    }
    form.vus = t.vus ?? 1
    form.vuStart = t.vuStart ?? 1
    form.duration = t.duration ?? 10
    form.requestDelay = t.requestDelay ?? null
    form.rampUp = t.rampUp ?? 0
    form.iterations = t.iterations ?? null
    form.bodyPreviewSize = t.bodyPreviewSize ?? 500
    form.vuUrlSuffix = Boolean(t.vuUrlSuffix ?? t.vu_url_suffix)
    const apiRules = parseErrorPageRulesFromPayload(t.errorPageRules ?? t.error_page_rules)
    if (Array.isArray(apiRules) && apiRules.length) {
      form.errorPageRules = apiRules.map((r) => ({
        pattern: r.pattern != null ? String(r.pattern) : '',
        matchMode:
          r.matchMode === 'not_contains' || r.match_mode === 'not_contains' ? 'not_contains' : 'contains',
      }))
    } else {
      const p = (t.errorPagePattern ?? t.error_page_pattern ?? '').trim()
      form.errorPageRules = p
        ? [
            {
              pattern: String(p).trim(),
              matchMode:
                t.errorPageMatchMode === 'not_contains' || t.error_page_match_mode === 'not_contains'
                  ? 'not_contains'
                  : 'contains',
            },
          ]
        : [{ pattern: '', matchMode: 'contains' }]
    }
    form.tags = normalizeTagList(t.tags)
    tagDraft.value = ''
    const actionsRaw = parseBrowserActionsFromPayload(t.browserActions ?? t.browser_actions)
    form.browserActions = actionsRaw.length
      ? actionsRaw.map((a) => browserActionRowFromApi(a))
      : form.engine === 'browser'
        ? [emptyBrowserActionRow()]
        : []
    syncUrlFromParams()
    if (form.engine === 'http') {
      scenarioSteps.value =
        Array.isArray(hs) && hs.length > 0 ? hs.map(stepFromApi) : [legacyHttpFieldsToScenarioStep(t)]
    } else {
      scenarioSteps.value = [emptyScenarioStep()]
    }
  } finally {
    applyingTestFromApi = false
  }
}

async function load() {
  if (!testId.value) return
  const myGen = ++remoteFormLoadGen
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${testId.value}`)
    if (myGen !== remoteFormLoadGen) return
    fillFormFromTest(t, false)
  } catch (err) {
    if (myGen === remoteFormLoadGen) loadError.value = getApiErrorMessage(err)
  } finally {
    if (myGen === remoteFormLoadGen) loading.value = false
  }
}

async function loadForClone() {
  if (!cloneFromId.value) return
  const myGen = ++remoteFormLoadGen
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${cloneFromId.value}`)
    if (myGen !== remoteFormLoadGen) return
    fillFormFromTest(t, true)
  } catch (err) {
    if (myGen === remoteFormLoadGen) loadError.value = getApiErrorMessage(err)
  } finally {
    if (myGen === remoteFormLoadGen) loading.value = false
  }
}

const urlPattern = /^https?:\/\/[^\s]+$/

function validate() {
  if (form.engine === 'browser') {
    parseUrlAndSyncToParams()
  }
  const e = {}
  delete errors.scenario
  delete errors.scenarioUrls
  delete errors.scenarioMultipart
  delete errors.scenarioPoll
  delete errors.browserActions
  if (!(form.name && form.name.trim())) e.name = '테스트 이름을 입력하세요.'
  const isHttpK6 = form.engine === 'http'
  if (isHttpK6) {
    const payload = buildHttpScenarioPayload()
    if (!payload.length) e.scenario = 'HTTP 단계에 URL이 있는 단계를 최소 1개 넣으세요.'
    const urlErrs = {}
    const mpErrs = {}
    const pollErrs = {}
    scenarioSteps.value.forEach((s, i) => {
      const u = (s.url || '').trim()
      if (!u) return
      if (!urlPattern.test(u)) urlErrs[i] = '유효한 URL 형식이 아닙니다.'
      if (s.bodyKind === 'multipart') {
        const fp = (s.multipartFilePath || '').trim()
        const ff = (s.multipartFileField || '').trim()
        if (!fp || !ff) {
          mpErrs[i] = '파일을 업로드하고 파일 필드명을 입력하세요.'
        }
        const m = String(s.method || 'GET').toUpperCase()
        if (!['POST', 'PUT', 'PATCH'].includes(m)) {
          mpErrs[i] = (mpErrs[i] ? `${mpErrs[i]} ` : '') + 'multipart는 POST·PUT·PATCH만 가능합니다.'
        }
      }
      if (s.pollEnabled) {
        const iv = Number(s.pollIntervalSeconds)
        const md = Number(s.pollMaxDurationSeconds)
        let msg = ''
        if (Number.isNaN(iv) || iv < 0.1 || iv > 60) {
          msg = '폴링 간격은 0.1~60초 사이 숫자여야 합니다.'
        } else if (Number.isNaN(md) || md < 0.5 || md > 600) {
          msg = '폴링 최대 시간은 0.5~600초 사이 숫자여야 합니다.'
        } else {
          const path = (s.pollUntilJsonPath || '').trim()
          const statuses = parsePollStatusInInput(s.pollUntilStatusIn)
          const hasJ = !!path
          const hasS = statuses.length > 0
          if (!hasJ && !hasS) {
            msg =
              '폴링: JSON 경로(및 기대 문자열) 또는 HTTP 상태 코드 목록(예: 200, 202) 중 하나는 필요합니다.'
          }
          if (!msg) {
            const wPath = (s.pollWhileJsonPath || '').trim()
            const wEqTrim = (s.pollWhileEquals != null ? String(s.pollWhileEquals) : '').trim()
            if (!wPath && wEqTrim !== '') {
              msg = '폴링: 진행 중 조건을 쓰려면 JSON 필드 경로를 입력하세요.'
            }
          }
        }
        if (msg) pollErrs[i] = msg
      }
    })
    if (Object.keys(urlErrs).length) e.scenarioUrls = urlErrs
    if (Object.keys(mpErrs).length) e.scenarioMultipart = mpErrs
    if (Object.keys(pollErrs).length) e.scenarioPoll = pollErrs
  } else if (form.engine === 'db') {
    const dsn = (form.baseUrl || '').trim()
    if (!dsn) e.baseUrl = '연결 문자열(DSN)을 입력하세요.'
    if (!(form.dbQuery && form.dbQuery.trim())) e.dbQuery = '실행할 SQL 쿼리를 입력하세요.'
  } else {
    const base = (form.baseUrl || '').trim()
    if (!base) e.baseUrl = '대상 URL을 입력하세요.'
    else if (!urlPattern.test(base)) e.baseUrl = '유효한 URL 형식이 아닙니다.'
    const baErrs = {}
    ;(form.browserActions || []).forEach((row, i) => {
      const kind = String(row.type || 'click').trim()
      if (kind === 'sleep') {
        if (row.sleepMs === '' || row.sleepMs === null) return
        const sm = Number(row.sleepMs)
        if (Number.isNaN(sm) || sm < 0 || sm > 30_000) {
          baErrs[i] = 'sleep: sleepMs는 0~30000(ms) 숫자여야 합니다.'
        }
      } else if (kind === 'wait_selector' || kind === 'click') {
        const sel = (row.selector || '').trim()
        if (!sel) return
        const to = Number(row.timeoutMs)
        let msg = ''
        if (Number.isNaN(to) || to < 1000 || to > 60_000) {
          msg = 'timeoutMs는 1000~60000(ms)여야 합니다.'
        }
        if (msg) baErrs[i] = msg
      }
    })
    if (Object.keys(baErrs).length) e.browserActions = baErrs
  }
  if (form.vus != null && (form.vus < 1 || !Number.isInteger(form.vus))) e.vus = '1 이상의 정수를 입력하세요.'
  if (form.vuStart != null && (form.vuStart < 1 || !Number.isInteger(form.vuStart))) e.vuStart = '1 이상의 정수를 입력하세요.'
  if (form.duration != null && (form.duration < 1 || !Number.isInteger(form.duration))) e.duration = '1 이상의 정수를 입력하세요.'
  if (form.rampUp != null && (form.rampUp < 0 || !Number.isInteger(form.rampUp))) e.rampUp = '0 이상의 정수를 입력하세요.'
  const iter = form.iterations
  const iterEmpty = (iter === null || iter === '' || (typeof iter === 'number' && Number.isNaN(iter)))
  if (!iterEmpty && (Number(iter) < 1 || !Number.isInteger(Number(iter)))) e.iterations = '1 이상의 정수를 입력하세요.'
  Object.assign(errors, e)
  return Object.keys(e).length === 0
}

async function onSubmit() {
  apiError.value = ''
  if (!validate()) return
  saving.value = true
  try {
    const isHttpK6 = form.engine === 'http'
    const isDb = form.engine === 'db'
    const scenarioPayload = isHttpK6 ? buildHttpScenarioPayload() : []
    if (isHttpK6 && !scenarioPayload.length) {
      apiError.value = 'HTTP 단계에 URL이 있는 단계가 필요합니다.'
      saving.value = false
      return
    }
    const engineVal = isDb ? 'db' : (form.engine === 'browser' ? 'browser' : 'http')
    const body = {
      name: form.name.trim(),
      engine: engineVal,
      targetUrl: isHttpK6 ? scenarioPayload[0].url : (form.baseUrl || '').trim(),
      queryParams: (isHttpK6 || isDb) ? '[]' : buildQueryParamsJson(),
      httpMethod: isHttpK6 ? scenarioPayload[0].method : (isDb ? 'QUERY' : form.httpMethod),
      requestBody: (isHttpK6 || isDb) ? '' : (form.requestBody?.trim() || undefined),
      headers: (isHttpK6 || isDb) ? '{}' : buildHeadersJson(),
      vus: Number(form.vus),
      vuStart: Number(form.vuStart),
      duration: Number(form.duration),
      requestDelay: form.requestDelay != null && form.requestDelay !== '' ? Number(form.requestDelay) : undefined,
      rampUp: Number(form.rampUp) >= 0 ? Number(form.rampUp) : 0,
      iterations: (() => {
        const i = form.iterations
        if (i === null || i === '' || (typeof i === 'number' && Number.isNaN(i))) return null
        const n = Number(i)
        return n >= 1 && Number.isInteger(n) ? n : null
      })(),
      bodyPreviewSize: Math.min(10000, Math.max(0, Number(form.bodyPreviewSize) || 500)),
      vuUrlSuffix: Boolean(form.vuUrlSuffix),
      errorPageRules: form.errorPageRules
        .map((r) => ({
          pattern: (r.pattern || '').trim(),
          matchMode: r.matchMode === 'not_contains' ? 'not_contains' : 'contains',
        }))
        .filter((r) => r.pattern),
      httpScenario: isHttpK6 ? scenarioPayload : [],
      browserActions: form.engine === 'browser' ? buildBrowserActionsPayload() : undefined,
      dbDriver: isDb ? (form.dbDriver || 'postgres') : undefined,
      dbQuery: isDb ? (form.dbQuery || '').trim() : undefined,
      tags: normalizeTagList(form.tags),
    }
    if (isEdit.value) {
      await put(`tests/${testId.value}`, body)
    } else {
      await post('tests', body)
    }
    router.push('/tests')
  } catch (err) {
    apiError.value = getApiErrorMessage(err)
  } finally {
    saving.value = false
  }
}

watch(
  () => [route.name, route.params.id, route.query.cloneFrom],
  () => {
    if (route.name === 'test-edit' && route.params.id) {
      load()
    } else if (route.name === 'test-create' && route.query.cloneFrom) {
      loadForClone()
    }
  },
  { immediate: true },
)

onMounted(() => {
  loadExistingTags()
})
</script>

<style scoped>
.test-form {
  width: 100%;
  max-width: 1200px;
}
@media (min-width: 600px) {
  .form-row-nowrap-sm {
    flex-wrap: nowrap !important;
  }
}
.field-col-shrink {
  min-width: 0;
}
.engine-col {
  min-width: 0;
}
.engine-radio {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
.checkbox-help-row {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 4px;
  min-width: 0;
  width: fit-content;
  max-width: 100%;
}
.checkbox-help-row__check {
  flex: 0 1 auto;
  min-width: 0;
}
.checkbox-help-row__tip {
  flex: 0 0 auto;
  align-self: center;
  line-height: 1;
}
.error-page-pattern-col {
  min-width: 0;
}
.error-page-mode-col {
  min-width: 200px;
}
.capture-tab-help .capture-code {
  font-size: 0.875em;
  padding: 1px 6px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
}
.poll-tab-help__list {
  list-style: disc;
}
.poll-tab-help__list li {
  margin-top: 4px;
}
.poll-tab-help__list li:first-child {
  margin-top: 0;
}
.label-tip-icon {
  vertical-align: middle;
}
.request-window {
  min-height: 120px;
}
.scenario-step-window {
  min-height: 100px;
}
.browser-action-card {
  border-bottom: 0.5px solid var(--border-default);
}
.scenario-step-url-col {
  min-width: 0;
}
.scenario-step-request-block {
  padding-bottom: 8px;
  border-bottom: 0.5px solid var(--border-default);
}
.kv-section {
  margin-bottom: 8px;
}
.kv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.kv-row:hover {
  background-color: color-mix(in srgb, var(--text-primary) 4%, transparent);
  border-radius: 4px;
}
.kv-row .param-check {
  flex: 0 0 40px;
}
.kv-row .kv-key {
  flex: 0 0 200px;
  min-width: 120px;
}
.kv-row .kv-value {
  flex: 1;
  min-width: 120px;
}
.textarea-col {
  padding: 0;
}
.tag-input-wrap {
  position: relative;
}
.tag-suggest-list {
  position: absolute;
  z-index: 20;
  left: 0;
  right: 0;
  top: 100%;
  margin: 4px 0 0;
  padding: 4px 0;
  list-style: none;
  max-height: 220px;
  overflow-y: auto;
  border-radius: 8px;
  border: 1px solid var(--border-default, rgba(0, 0, 0, 0.12));
  background: var(--surface-elevated, var(--bg-default, #fff));
  box-shadow: 0 4px 12px color-mix(in srgb, var(--text-primary, #000) 12%, transparent);
}
.tag-suggest-list__item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.875rem;
}
.tag-suggest-list__item:hover,
.tag-suggest-list__item--active {
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
}
.scenario-multipart-file-input {
  display: none;
}
.multipart-file-name {
  word-break: break-all;
}
.multipart-filename-field :deep(.ui-text-field__row) {
  flex-wrap: wrap;
}
@media (min-width: 600px) {
  .multipart-filename-vu-btn {
    white-space: nowrap;
    font-size: 0.75rem;
    padding: 4px 8px;
  }
}
</style>
