<template>
  <div>
    <h1 class="text-h5 mb-2">{{ isEdit ? '테스트 수정' : '테스트 생성' }}</h1>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
    <v-alert v-else-if="loadError" type="error" density="compact" class="mb-2">{{ loadError }}</v-alert>
    <v-form v-else @submit.prevent="onSubmit" class="test-form compact-form">
      <v-row dense class="align-center mb-2 form-row-nowrap-sm">
        <v-col cols="12" sm="5" md="4" class="field-col-shrink">
          <v-text-field
            v-model="form.name"
            required
            density="compact"
            hide-details="auto"
            :error-messages="errors.name ? [errors.name] : []"
            label="테스트 이름"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>나중에 구분하기 위한 이름입니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="12" sm="7" md="8" class="d-flex align-center flex-nowrap ga-3 engine-col">
          <span class="text-body-2 text-medium-emphasis flex-shrink-0 d-none d-sm-inline">실행 방식</span>
          <v-radio-group
            v-model="form.engine"
            inline
            density="compact"
            hide-details
            class="engine-radio flex-grow-1"
          >
            <v-radio label="k6 (HTTP)" value="http" />
            <v-radio label="브라우저 (렌더링)" value="browser" />
          </v-radio-group>
        </v-col>
      </v-row>

      <v-row v-if="form.engine === 'http'" dense class="align-center mb-2 form-row-nowrap-sm checkbox-options-row">
        <v-col cols="12" md="6" class="checkbox-help-row pe-md-6">
          <v-checkbox
            v-model="scenarioMode"
            label="다단계 시나리오 (k6)"
            density="compact"
            hide-details
            class="checkbox-help-row__check"
          />
          <v-tooltip location="top" max-width="320" class="checkbox-help-row__tip">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>각 VU가 같은 단계를 순서대로 실행합니다. 이전 응답 JSON을 path로 꺼내 다음 단계 URL·헤더·본문에 변수로 넣을 수 있습니다.</span>
          </v-tooltip>
        </v-col>
        <v-col cols="12" md="6" class="checkbox-help-row">
          <v-checkbox
            v-model="form.vuUrlSuffix"
            label="경로 끝에 VU 번호 붙이기"
            density="compact"
            hide-details
            class="checkbox-help-row__check"
          />
          <v-tooltip location="top" class="checkbox-help-row__tip">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>예: /a/b/ccc → /a/b/ccc1, ccc2. 시나리오면 각 단계 URL에 적용됩니다.</span>
          </v-tooltip>
        </v-col>
      </v-row>

      <v-row v-if="!scenarioMode || form.engine !== 'http'" dense class="align-center mb-2 form-row-nowrap-sm">
        <v-col cols="12" sm="3" md="2" class="flex-shrink-0">
          <v-select
            v-model="form.httpMethod"
            :items="['GET', 'POST', 'PUT', 'PATCH', 'DELETE']"
            density="compact"
            hide-details
            label="HTTP 메서드"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>요청 방식입니다. 보통 조회는 GET, 데이터 전송은 POST를 씁니다.</span>
              </v-tooltip>
            </template>
          </v-select>
        </v-col>
        <v-col cols="12" sm="9" md="10" style="min-width: 0">
          <v-text-field
            :model-value="urlDisplay"
            placeholder="https://example.com?a=b"
            density="compact"
            hide-details="auto"
            :error-messages="errors.baseUrl ? [errors.baseUrl] : []"
            label="대상 URL"
            @update:model-value="urlDisplay = $event"
            @blur="parseUrlAndSyncToParams"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>부하를 줄 주소입니다. VU별로 다르게 하려면 경로에 <code>{{ vuPlaceholder }}</code>를 넣거나 위 옵션을 사용하세요.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
      </v-row>

      <v-row v-if="scenarioMode && form.engine === 'http'" dense class="mt-2">
        <v-col cols="12">
          <p class="text-subtitle-2 mb-2">HTTP 단계</p>
          <v-card
            v-for="(step, si) in scenarioSteps"
            :key="si"
            variant="outlined"
            class="mb-3 pa-3 scenario-step-card"
          >
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-body-2 font-weight-medium">단계 {{ si + 1 }}</span>
              <v-btn
                icon
                variant="text"
                size="small"
                color="error"
                :disabled="scenarioSteps.length <= 1"
                @click="removeScenarioStep(si)"
              >
                <v-icon size="small">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
            <div class="scenario-step-request-block mb-3">
              <v-row dense>
                <v-col cols="12" md="6" lg="4">
                  <v-text-field
                    v-model="step.name"
                    label="단계 이름 (선택)"
                    placeholder="login"
                    density="compact"
                    hide-details="auto"
                  />
                </v-col>
              </v-row>
              <v-row dense class="form-row-nowrap-sm">
                <v-col cols="12" sm="3" md="2" class="flex-shrink-0">
                  <v-select
                    v-model="step.method"
                    :items="['GET', 'POST', 'PUT', 'PATCH', 'DELETE']"
                    label="메서드"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" sm="9" md="10" class="scenario-step-url-col">
                  <v-text-field
                    v-model="step.url"
                    label="URL (쿼리는 아래 Params 탭)"
                    placeholder="https://api.example.com/v1/..."
                    density="compact"
                    hide-details="auto"
                    :error-messages="errors.scenarioUrls && errors.scenarioUrls[si] ? [errors.scenarioUrls[si]] : []"
                  />
                </v-col>
              </v-row>
              <v-row dense class="mt-1">
                <v-col cols="12" sm="6" md="4">
                  <v-text-field
                    v-model="step.sleepAfterSeconds"
                    label="다음 스텝 전 대기(초)"
                    type="number"
                    min="0"
                    max="600"
                    step="0.1"
                    density="compact"
                    hide-details="auto"
                    hint="0 또는 비움 = 스텝 간 대기 없음. 이 단계 응답·기록 직후 적용."
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </div>
            <v-tabs v-model="step.scenarioTab" density="compact" class="scenario-step-tabs mb-2">
              <v-tab value="params">Params</v-tab>
              <v-tab value="headers">Headers</v-tab>
              <v-tab value="body">Body</v-tab>
              <v-tab value="capture">캡처</v-tab>
            </v-tabs>
            <v-window v-model="step.scenarioTab" class="scenario-step-window">
              <v-window-item value="params">
                <div class="kv-section">
                  <div v-for="(row, pi) in step.paramsList" :key="pi" class="kv-row">
                    <v-checkbox
                      v-model="row.enabled"
                      hide-details
                      density="compact"
                      class="param-check flex-shrink-0"
                    />
                    <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" />
                    <v-text-field
                      v-model="row.value"
                      :placeholder="`Value (VU별: ${vuPlaceholder})`"
                      density="compact"
                      hide-details
                      class="kv-value"
                    />
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      :disabled="step.paramsList.length <= 1"
                      @click="removeScenarioParam(si, pi)"
                    >
                      <v-icon size="small">mdi-delete-outline</v-icon>
                    </v-btn>
                  </div>
                  <v-btn size="small" variant="tonal" class="mt-1" @click="addScenarioParam(si)">추가</v-btn>
                </div>
              </v-window-item>
              <v-window-item value="headers">
                <div class="kv-section">
                  <div v-for="(row, hi) in step.headersList" :key="hi" class="kv-row">
                    <v-checkbox v-model="row.enabled" hide-details density="compact" class="param-check flex-shrink-0" />
                    <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" />
                    <v-text-field
                      v-model="row.value"
                      :placeholder="`Value (VU별: ${vuPlaceholder})`"
                      density="compact"
                      hide-details
                      class="kv-value"
                    />
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      :disabled="step.headersList.length <= 1"
                      @click="removeScenarioHeader(si, hi)"
                    >
                      <v-icon size="small">mdi-delete-outline</v-icon>
                    </v-btn>
                  </div>
                  <v-btn size="small" variant="tonal" class="mt-1" @click="addScenarioHeader(si)">헤더 추가</v-btn>
                </div>
              </v-window-item>
              <v-window-item value="body">
                <div class="textarea-col">
                  <v-textarea
                    v-model="step.body"
                    :placeholder="`요청 본문. VU별: ${vuPlaceholder} 삽입 가능`"
                    rows="4"
                    density="compact"
                    hide-details
                    auto-grow
                  />
                </div>
              </v-window-item>
              <v-window-item value="capture">
                <v-alert type="info" density="compact" variant="tonal" class="mb-3 capture-tab-help">
                  <div class="text-body-2">
                    HTTP <strong>2xx</strong>일 때만 값을 꺼냅니다.
                    <strong>JSON 본문</strong>: 응답을 JSON으로 파싱한 뒤 점(.) 경로로 필드를 고릅니다.
                    <strong>응답 헤더</strong>: 헤더 이름(key)으로 조회합니다(대소문자 무시). Set-Cookie는
                    <strong>쿠키 이름(선택)</strong>을 넣으면 <code class="capture-code">access_token=…; Path=/</code>에서 값(… )만 잘라 씁니다.
                    그다음 단계 URL·Params·Headers·Body에
                    <code v-pre class="capture-code">{{변수명}}</code>을 넣으면 치환됩니다. 변수명·JSON 경로·헤더 이름을 모두 비우면 캡처하지 않습니다.
                  </div>
                </v-alert>
                <v-row dense class="mb-2">
                  <v-col cols="12" sm="6">
                    <v-select
                      v-model="step.captureFrom"
                      :items="captureSourceItems"
                      item-title="title"
                      item-value="value"
                      label="캡처 출처"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="step.captureVar"
                      label="변수명"
                      placeholder="token"
                      hint="영문·숫자·밑줄. 다음 단계에 {{ 이름 }} 형태로 사용."
                      persistent-hint
                      density="compact"
                      hide-details="auto"
                    />
                  </v-col>
                </v-row>
                <v-row dense>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-if="step.captureFrom !== 'header'"
                      v-model="step.capturePath"
                      label="JSON 경로 (path)"
                      placeholder="예: access_token, data.id"
                      hint="응답 JSON 루트부터의 키 경로. 배열 인덱스(n)는 미지원."
                      persistent-hint
                      density="compact"
                      hide-details="auto"
                    />
                    <v-text-field
                      v-else
                      v-model="step.captureHeader"
                      label="응답 헤더 이름"
                      placeholder="예: X-Request-Id, Set-Cookie"
                      hint="실제 응답 헤더 키와 대소문자만 다르면 같은 것으로 봅니다."
                      persistent-hint
                      density="compact"
                      hide-details="auto"
                    />
                  </v-col>
                  <v-col v-if="step.captureFrom === 'header'" cols="12" sm="6">
                    <v-text-field
                      v-model="step.captureCookieName"
                      label="쿠키 이름 (선택)"
                      placeholder="예: access_token"
                      hint="Set-Cookie 한 줄에서 이 이름의 값만 사용. 비우면 헤더 값 전체를 변수에 넣습니다."
                      persistent-hint
                      density="compact"
                      hide-details="auto"
                    />
                  </v-col>
                </v-row>
              </v-window-item>
            </v-window>
          </v-card>
          <v-btn size="small" variant="tonal" @click="addScenarioStep">단계 추가</v-btn>
        </v-col>
      </v-row>
      <template v-if="!(scenarioMode && form.engine === 'http')">
      <br/>
      <v-tabs v-model="requestTab" density="compact" class="request-tabs mb-2">
        <v-tab value="params">
          Params
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>URL 뒤에 붙는 검색 조건(쿼리)입니다. (예: ?page=1)</span>
          </v-tooltip>
        </v-tab>
        <v-tab value="headers">
          Headers
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>요청에 넣는 부가 정보입니다. (인증 토큰, Content-Type 등)</span>
          </v-tooltip>
        </v-tab>
        <v-tab value="body">
          Body
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" size="x-small" class="ml-1 label-tip-icon">mdi-information-outline</v-icon>
            </template>
            <span>POST/PUT 등으로 보낼 본문 내용(JSON 등)입니다.</span>
          </v-tooltip>
        </v-tab>
      </v-tabs>
      <v-window v-model="requestTab" class="request-window">
        <v-window-item value="params">
          <div class="kv-section">
            <div v-for="(row, i) in form.paramsList" :key="i" class="kv-row">
              <v-checkbox
                v-model="row.enabled"
                hide-details
                density="compact"
                class="param-check flex-shrink-0"
                @update:model-value="syncUrlFromParams"
              />
              <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" @update:model-value="syncUrlFromParams" />
              <v-text-field v-model="row.value" :placeholder="`Value (VU별: value-${vuPlaceholder})`" density="compact" hide-details class="kv-value" @update:model-value="syncUrlFromParams" />
              <v-btn icon variant="text" size="small" color="error" :disabled="form.paramsList.length <= 1" @click="removeParam(i)">
                <v-icon size="small">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
            <v-btn size="small" variant="tonal" class="mt-1" @click="addParam">추가</v-btn>
          </div>
        </v-window-item>
        <v-window-item value="headers">
          <div class="kv-section">
            <div v-for="(row, i) in form.headersList" :key="i" class="kv-row">
              <v-checkbox
                v-model="row.enabled"
                hide-details
                density="compact"
                class="param-check flex-shrink-0"
              />
              <v-text-field v-model="row.key" placeholder="Key" density="compact" hide-details class="kv-key" />
              <v-text-field v-model="row.value" :placeholder="`Value (VU별: value-${vuPlaceholder})`" density="compact" hide-details class="kv-value" />
              <v-btn icon variant="text" size="small" color="error" :disabled="form.headersList.length <= 1" @click="removeHeader(i)">
                <v-icon size="small">mdi-delete-outline</v-icon>
              </v-btn>
            </div>
            <v-btn size="small" variant="tonal" class="mt-1" @click="addHeader">추가</v-btn>
          </div>
        </v-window-item>
        <v-window-item value="body">
          <div class="textarea-col">
            <v-textarea
              v-model="form.requestBody"
              :placeholder="`요청 본문 입력. VU마다 다르게 하려면 본문에 ${vuPlaceholder}를 넣으세요.`"
              rows="4"
              density="compact"
              hide-details
              auto-grow
            />
          </div>
        </v-window-item>
      </v-window>
      </template>
      <v-row dense class="load-settings-row mt-3">
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.vus"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.vus ? [errors.vus] : []"
            label="VUs"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>동시에 요청을 보내는 '가상 사용자' 수입니다. 10이면 10명이 동시에 접속한 것처럼 테스트합니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.vuStart"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.vuStart ? [errors.vuStart] : []"
            :label="`${vuPlaceholder} 시작 번호`"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>k6에서 첫 번째 VU(__VU=1)에 URL·본문 등의 {{ vuPlaceholder }} 자리에 들어갈 숫자입니다. 이후 VU는 1씩 증가합니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.duration"
            type="number"
            min="1"
            density="compact"
            hide-details="auto"
            :error-messages="errors.duration ? [errors.duration] : []"
            label="제한 시간(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트가 실행될 수 있는 최대 시간(초)입니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.requestDelay"
            type="number"
            min="0"
            step="0.1"
            density="compact"
            hide-details
            label="대기(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>한 번 요청을 보낸 뒤, 다음 요청 전에 기다리는 시간(초)입니다. 0이면 쉬지 않고 연속 요청합니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.rampUp"
            type="number"
            min="0"
            density="compact"
            hide-details
            label="Ramp-up(초)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>테스트 시작 시 가상 사용자를 0에서 설정한 수까지 서서히 늘리는 시간입니다. 서버에 부담을 줄일 수 있습니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.iterations"
            type="number"
            min="1"
            placeholder="비우면 제한 시간만큼"
            density="compact"
            hide-details="auto"
            :error-messages="errors.iterations ? [errors.iterations] : []"
            label="반복 횟수 (선택)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>각 가상 사용자가 요청을 보낼 횟수입니다. 비워두면 제한 시간(초) 동안만 반복합니다. 입력 시 1 이상의 정수.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
        <v-col cols="6" sm="4" md="2">
          <v-text-field
            v-model.number="form.bodyPreviewSize"
            type="number"
            min="0"
            max="10000"
            density="compact"
            hide-details
            label="결과 화면 본문 표시(자)"
          >
            <template #append>
              <v-tooltip location="top">
                <template #activator="{ props }">
                  <v-icon v-bind="props" size="small" class="label-tip-icon">mdi-information-outline</v-icon>
                </template>
                <span>실행 결과 목록·호버에서 응답 본문을 잘라 보여줄 글자 수입니다. DB에는 응답 본문 전체가 저장됩니다. 0이면 목록에는 …만 보이고 호버로 전체를 볼 수 있습니다.</span>
              </v-tooltip>
            </template>
          </v-text-field>
        </v-col>
      </v-row>
      <div class="mt-2 error-page-section">
        <div class="text-caption text-medium-emphasis mb-1">
          에러 페이지 판별 (URL·응답 본문). 조건을 여러 개 두면 <strong>하나라도</strong> 실패 조건이면 해당 요청이 실패로 집계됩니다.
        </div>
        <v-row
          v-for="(row, idx) in form.errorPageRules"
          :key="'err-' + idx"
          dense
          class="align-end form-row-nowrap-sm error-page-row"
        >
          <v-col cols="12" sm="5" md="4" class="flex-shrink-0 error-page-mode-col">
            <v-select
              v-model="row.matchMode"
              label="판별 방식"
              :items="errorMatchModeItems"
              item-title="title"
              item-value="value"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="6" md="7" class="error-page-pattern-col">
            <v-text-field
              v-model="row.pattern"
              label="판별 문자열"
              placeholder="비우면 이 줄은 무시"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="1" md="1" class="d-flex align-center error-page-actions-col">
            <v-btn
              v-if="form.errorPageRules.length > 1"
              icon="mdi-delete-outline"
              variant="text"
              size="small"
              density="compact"
              aria-label="조건 삭제"
              @click="removeErrorPageRule(idx)"
            />
            <v-btn
              v-if="idx === form.errorPageRules.length - 1"
              icon="mdi-plus"
              variant="text"
              size="small"
              density="compact"
              aria-label="조건 추가"
              @click="addErrorPageRule"
            />
          </v-col>
        </v-row>
      </div>
      <div class="d-flex align-center flex-wrap mt-2">
        <v-btn type="submit" color="primary" :loading="saving" size="small" class="mr-2">저장</v-btn>
        <v-btn v-if="isEdit" :to="`/tests/${testId}/run`" variant="text" color="primary" size="small" class="mr-2">실행</v-btn>
        <v-btn to="/tests" variant="text" size="small">목록으로</v-btn>
      </div>
      <v-alert v-if="apiError" type="error" density="compact" class="mt-2">{{ apiError }}</v-alert>
    </v-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post, put, getApiErrorMessage } from '../services/api'

const vuPlaceholder = '{{VU}}'
const errorMatchModeItems = [
  { title: '판별 문구가 있으면 실패', value: 'contains' },
  { title: '판별 문구가 없으면 실패', value: 'not_contains' },
]
const captureSourceItems = [
  { title: 'JSON 본문 (path)', value: 'json' },
  { title: '응답 헤더', value: 'header' },
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
const errors = reactive({})
const requestTab = ref('params')
const urlDisplay = ref('')

function emptyScenarioStep() {
  return {
    name: '',
    method: 'GET',
    url: '',
    scenarioTab: 'params',
    paramsList: [{ key: '', value: '', enabled: false }],
    headersList: [{ key: '', value: '', enabled: false }],
    body: '',
    captureFrom: 'json',
    capturePath: '',
    captureHeader: '',
    captureCookieName: '',
    captureVar: '',
    sleepAfterSeconds: '',
  }
}

const scenarioMode = ref(false)
const scenarioSteps = ref([emptyScenarioStep()])

/** 다단계 켜질 때 첫 단계 URL이 비어 있으면 단일 요청 폼 값을 복사 */
function seedFirstScenarioStepFromForm() {
  if (form.engine !== 'http') return
  const first = scenarioSteps.value[0]
  if (!first || (first.url || '').trim()) return
  first.method = form.httpMethod || 'GET'
  first.url = (form.baseUrl || '').trim()
  first.paramsList = JSON.parse(JSON.stringify(form.paramsList || [{ key: '', value: '', enabled: false }]))
  first.headersList = JSON.parse(JSON.stringify(form.headersList || [{ key: '', value: '', enabled: false }]))
  first.body = form.requestBody != null ? String(form.requestBody) : ''
}

function addScenarioStep() {
  scenarioSteps.value.push(emptyScenarioStep())
}

function removeScenarioStep(i) {
  if (scenarioSteps.value.length <= 1) return
  scenarioSteps.value.splice(i, 1)
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
  return {
    name: s.name || '',
    method: s.method || 'GET',
    url: s.url || '',
    scenarioTab: 'params',
    paramsList,
    headersList: hEntries.length
      ? hEntries.map(([k, v]) => ({ key: k, value: String(v ?? ''), enabled: true }))
      : [{ key: '', value: '', enabled: false }],
    body: s.body || '',
    captureFrom: s.capture && String(s.capture.from || '').toLowerCase() === 'header' ? 'header' : 'json',
    capturePath: s.capture?.path || '',
    captureHeader: s.capture?.header || '',
    captureCookieName: s.capture?.cookieName || '',
    captureVar: s.capture?.var || '',
    sleepAfterSeconds:
      s.sleepAfterSeconds != null && s.sleepAfterSeconds !== '' ? String(s.sleepAfterSeconds) : '',
  }
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
    const b = (s.body || '').trim()
    if (b) row.body = b
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
})

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

watch(
  () => [form.baseUrl, form.paramsList],
  () => { syncUrlFromParams() },
  { deep: true }
)

watch(
  () => form.engine,
  (e) => {
    if (e === 'browser') scenarioMode.value = false
  }
)

watch(scenarioMode, (on, prev) => {
  if (on && prev === false && form.engine === 'http') {
    seedFirstScenarioStepFromForm()
  }
})

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

function parseQueryParamsToList(str) {
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

function parseHeadersToList(str) {
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

function fillFormFromTest(t, clone = false) {
  form.name = clone ? `복사 - ${t.name ?? ''}` : (t.name ?? '')
  form.engine = (t.engine === 'browser' ? 'browser' : 'http')
  form.baseUrl = t.targetUrl ?? ''
  form.paramsList = parseQueryParamsToList(t.queryParams ?? '')
  form.httpMethod = t.httpMethod ?? 'GET'
  form.requestBody = t.requestBody ?? ''
  form.headersList = parseHeadersToList(t.headers ?? '')
  form.vus = t.vus ?? 1
  form.vuStart = t.vuStart ?? 1
  form.duration = t.duration ?? 10
  form.requestDelay = t.requestDelay ?? null
  form.rampUp = t.rampUp ?? 0
  form.iterations = t.iterations ?? null
  form.bodyPreviewSize = t.bodyPreviewSize ?? 500
  form.vuUrlSuffix = t.vuUrlSuffix ?? false
  const apiRules = t.errorPageRules
  if (Array.isArray(apiRules) && apiRules.length) {
    form.errorPageRules = apiRules.map((r) => ({
      pattern: r.pattern != null ? String(r.pattern) : '',
      matchMode: r.matchMode === 'not_contains' ? 'not_contains' : 'contains',
    }))
  } else {
    const p = (t.errorPagePattern || '').trim()
    form.errorPageRules = p
      ? [{ pattern: String(t.errorPagePattern ?? '').trim(), matchMode: t.errorPageMatchMode === 'not_contains' ? 'not_contains' : 'contains' }]
      : [{ pattern: '', matchMode: 'contains' }]
  }
  syncUrlFromParams()
  const hs = t.httpScenario
  if (form.engine === 'http' && Array.isArray(hs) && hs.length > 0) {
    scenarioMode.value = true
    scenarioSteps.value = hs.map(stepFromApi)
  } else {
    scenarioMode.value = false
    scenarioSteps.value = [emptyScenarioStep()]
  }
}

async function load() {
  if (!testId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${testId.value}`)
    fillFormFromTest(t, false)
  } catch (err) {
    loadError.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function loadForClone() {
  if (!cloneFromId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const t = await get(`tests/${cloneFromId.value}`)
    fillFormFromTest(t, true)
  } catch (err) {
    loadError.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

const urlPattern = /^https?:\/\/[^\s]+$/

function validate() {
  parseUrlAndSyncToParams()
  const e = {}
  delete errors.scenario
  delete errors.scenarioUrls
  if (!(form.name && form.name.trim())) e.name = '테스트 이름을 입력하세요.'
  const scenarioActive = form.engine === 'http' && scenarioMode.value
  if (scenarioActive) {
    const payload = buildHttpScenarioPayload()
    if (!payload.length) e.scenario = '시나리오에 URL이 있는 단계를 최소 1개 넣으세요.'
    const urlErrs = {}
    scenarioSteps.value.forEach((s, i) => {
      const u = (s.url || '').trim()
      if (!u) return
      if (!urlPattern.test(u)) urlErrs[i] = '유효한 URL 형식이 아닙니다.'
    })
    if (Object.keys(urlErrs).length) e.scenarioUrls = urlErrs
  } else {
    const base = (form.baseUrl || '').trim()
    if (!base) e.baseUrl = '대상 URL을 입력하세요.'
    else if (!urlPattern.test(base)) e.baseUrl = '유효한 URL 형식이 아닙니다.'
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
    const isScenario = form.engine === 'http' && scenarioMode.value
    const scenarioPayload = isScenario ? buildHttpScenarioPayload() : []
    if (isScenario && !scenarioPayload.length) {
      apiError.value = '시나리오에 URL이 있는 단계가 필요합니다.'
      saving.value = false
      return
    }
    const body = {
      name: form.name.trim(),
      engine: (form.engine === 'browser' ? 'browser' : 'http'),
      targetUrl: isScenario ? scenarioPayload[0].url : (form.baseUrl || '').trim(),
      queryParams: isScenario ? '[]' : buildQueryParamsJson(),
      httpMethod: isScenario ? scenarioPayload[0].method : form.httpMethod,
      requestBody: isScenario ? '' : (form.requestBody?.trim() || undefined),
      headers: isScenario ? '{}' : buildHeadersJson(),
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
      httpScenario: form.engine === 'http' ? (isScenario ? scenarioPayload : []) : [],
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

onMounted(() => {
  if (isEdit.value) load()
  else if (cloneFromId.value) loadForClone()
  else syncUrlFromParams()
})
</script>

<style scoped>
.test-form { width: 100%; max-width: 1200px; }
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
.engine-radio :deep(.v-input__control) {
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
}
.engine-radio :deep(.v-selection-control-group) {
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center;
  gap: 4px;
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
.checkbox-help-row__check :deep(.v-input),
.checkbox-help-row__check :deep(.v-selection-control) {
  width: auto;
  max-width: 100%;
}
.checkbox-help-row__tip {
  flex: 0 0 auto;
  align-self: center;
  line-height: 1;
}
.checkbox-help-row__tip :deep(.v-icon) {
  display: block;
}
.checkbox-help-row :deep(.v-label) {
  white-space: nowrap;
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
  background: rgba(0, 0, 0, 0.06);
}
.label-tip-icon { vertical-align: middle; }
.label-tip-icon:hover { background-color: #e0e0e0 !important; color: #1a1a1a !important; border-radius: 50%; }
.label-with-tip { user-select: none; -webkit-user-select: none; }
.label-with-tip:hover { color: #1a1a1a; background-color: rgba(255, 255, 255, 0.95); border-radius: 4px; }
.compact-form :deep(.v-field),
.compact-form :deep(.v-field__input),
.compact-form :deep(input),
.compact-form :deep(textarea) { font-size: 1rem; }
.compact-form :deep(.v-field .v-label),
.compact-form :deep(.v-field__outline .v-label) { transition: none !important; }

.request-tabs { min-height: 36px; }
/* 마우스 올렸을 때만: 밝은 배경 + 진한 글씨 */
.request-tabs :deep(.v-tab:hover),
.request-tabs :deep(.v-tab:hover::before),
.request-tabs :deep(.v-tab .v-btn:hover),
.request-tabs :deep(.v-tab .v-btn:hover::before),
.request-tabs :deep(.v-tab .v-btn__overlay),
.request-tabs :deep(.v-tab:hover .v-btn__overlay) { background-color: #e8e8e8 !important; background: #e8e8e8 !important; color: #1a1a1a !important; opacity: 1 !important; }
.request-tabs :deep(.v-tab:hover .v-icon),
.request-tabs :deep(.v-tab .v-btn:hover .v-icon) { color: #1a1a1a !important; }
.request-window { min-height: 120px; }
.scenario-step-tabs { min-height: 36px; }
.scenario-step-tabs :deep(.v-tab:hover),
.scenario-step-tabs :deep(.v-tab:hover::before),
.scenario-step-tabs :deep(.v-tab .v-btn:hover),
.scenario-step-tabs :deep(.v-tab .v-btn:hover::before),
.scenario-step-tabs :deep(.v-tab .v-btn__overlay),
.scenario-step-tabs :deep(.v-tab:hover .v-btn__overlay) { background-color: #e8e8e8 !important; background: #e8e8e8 !important; color: #1a1a1a !important; opacity: 1 !important; }
.scenario-step-tabs :deep(.v-tab:hover .v-icon),
.scenario-step-tabs :deep(.v-tab .v-btn:hover .v-icon) { color: #1a1a1a !important; }
.scenario-step-window { min-height: 100px; }
.scenario-step-url-col {
  min-width: 0;
}
.scenario-step-request-block {
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
.kv-section { margin-bottom: 8px; }
.kv-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.kv-row:hover { background-color: rgba(0, 0, 0, 0.04); border-radius: 4px; }
.kv-row:hover :deep(.v-field),
.kv-row:hover :deep(.v-field__input),
.kv-row:hover :deep(input),
.kv-row :deep(.v-checkbox:hover .v-label),
.kv-row :deep(.v-checkbox .v-label) { color: #1a1a1a !important; }
.kv-row .param-check { flex: 0 0 40px; }
.kv-row .kv-key { flex: 0 0 200px; min-width: 120px; }
.kv-row .kv-value { flex: 1; min-width: 120px; }
.textarea-col { padding: 0; }
.textarea-col :deep(.v-field) { align-items: flex-start; }
</style>
